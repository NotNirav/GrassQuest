"""Expand quest templates into concrete quests and embed each template with local bge-m3.

  python -m scripts.build_quests          # writes app/data/quests_v2.json + app/data/templates_v2.json
  python -m scripts.build_quests --load   # also upserts both into MongoDB and creates the vector index

Run from server/. Needs Ollama with bge-m3 for the embeddings.
"""
import itertools
import json
import re
import sys
import urllib.request

from scripts.quest_templates import T

OLLAMA = "http://localhost:11434"
OUT = "app/data"

# Optional twists multiply variety. Each adds effort and changes the quest enough to feel new.
TWISTS = [
    {"id": "", "suffix": "", "effort": 0, "min": 0, "ok": lambda t: True},
    {"id": "friend", "suffix": ", with a friend", "effort": 1, "min": 5, "ok": lambda t: t["cat"] not in ("social", "rain", "mindful")},
    {"id": "newroute", "suffix": ", taking a route you've never used", "effort": 1, "min": 10, "ok": lambda t: t["cat"] in ("move", "explore", "nature", "water", "birds") and not t.get("rain")},
    {"id": "nophone", "suffix": ", phone in your pocket until you find it", "effort": 1, "min": 0, "ok": lambda t: t["cat"] in ("nature", "birds", "explore", "photo", "sky") and not t.get("rain")},
    {"id": "speed", "suffix": ", in under 15 minutes", "effort": 1, "min": -5, "ok": lambda t: t["effort"] <= 2 and t["min"] >= 10 and not t.get("rain")},
]


def rarity(effort: int) -> str:
    return "common" if effort <= 2 else "rare" if effort == 3 else "legendary"


def slug(v) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(v).lower()).strip("-")


def fill(text: str, values: dict) -> str:
    for k, v in values.items():
        text = text.replace("{" + k + "}", str(v))
    return text


def expand():
    quests = []
    for t in T:
        keys = list(t.get("params", {}))
        combos = [dict(zip(keys, vals)) for vals in itertools.product(*[t["params"][k] for k in keys])] or [{}]
        for values in combos:
            for tw in TWISTS:
                if not tw["ok"](t):
                    continue
                effort = min(5, t["effort"] + tw["effort"])
                qid = "-".join(p for p in [t["id"], *(slug(v) for v in values.values()), tw["id"]] if p)
                quests.append({
                    "_id": qid, "id": qid, "template_id": t["id"],
                    "title": fill(t["t"], values) + tw["suffix"],
                    "cat": t["cat"], "needs": t.get("needs", []), "effort": effort, "rarity": rarity(effort),
                    "minutes": max(3, t["min"] + tw["min"]), "time": t.get("time", "any"),
                    "wet": bool(t.get("wet")), "rain": bool(t.get("rain")), "kind": t.get("kind", "none"),
                    "proof": fill(t["proof"], values), "twist": tw["id"] or None,
                })
    return quests


def embed(text: str) -> list[float]:
    req = urllib.request.Request(f"{OLLAMA}/api/embed", json.dumps({"model": "bge-m3", "input": text}).encode(),
                                 {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())["embeddings"][0]


def main():
    quests = expand()
    # reuse embeddings from the last build; only new templates go to bge-m3
    try:
        old = {x["_id"]: x["embedding"] for x in json.load(open(f"{OUT}/templates_v2.json", encoding="utf-8"))}
    except FileNotFoundError:
        old = {}
    templates = []
    for i, t in enumerate(T):
        emb = old.get(t["id"]) or embed(f"{t['t']}. {t['proof']}")
        templates.append({"_id": t["id"], "id": t["id"], "title": t["t"], "cat": t["cat"], "embedding": emb})
        if t["id"] not in old:
            print(f"embedded {i + 1}/{len(T)} {t['id']}", flush=True)
    json.dump(quests, open(f"{OUT}/quests_v2.json", "w", encoding="utf-8"))
    json.dump(templates, open(f"{OUT}/templates_v2.json", "w", encoding="utf-8"))
    by_cat = {}
    for q in quests:
        by_cat[q["cat"]] = by_cat.get(q["cat"], 0) + 1
    print(f"{len(T)} templates -> {len(quests)} quests", by_cat)

    if "--load" in sys.argv:
        from pymongo import ReplaceOne
        from app import db

        db.quests.delete_many({})
        db.quests.bulk_write([ReplaceOne({"_id": q["_id"]}, q, upsert=True) for q in quests])
        db.templates.delete_many({})
        db.templates.bulk_write([ReplaceOne({"_id": t["_id"]}, t, upsert=True) for t in templates])
        db.quests.create_index([("cat", 1), ("effort", 1)])
        print(f"loaded into {'Atlas' if db.USING_ATLAS else 'in-memory db'}")
        if db.USING_ATLAS:
            from pymongo.operations import SearchIndexModel

            if "template_embedding_index" not in [i["name"] for i in db.templates.list_search_indexes()]:
                db.templates.create_search_index(SearchIndexModel(
                    name="template_embedding_index", type="vectorSearch",
                    definition={"fields": [{"type": "vector", "path": "embedding", "numDimensions": 1024, "similarity": "cosine"}]},
                ))
                print("created template vector index")


if __name__ == "__main__":
    main()
