# 🌿 Side Quests

Tiny real-world quests that get you off the screen. Get a quest, go outside, come back with a photo, and **Gemma, an open-weight model running on your own computer through Ollama**, judges whether you did it. Your photo never leaves your machine.

Built for the DEV **Hacktoberfest Open-Source AI Challenge, Week 1: "Touch Grass"** (Oct 2026).

## How it works

```
 Browser (React)                                   Your computer
 ┌───────────────────────────────┐   photo +      ┌──────────────────────────┐
 │ quest card · "go outside"     │ ── prompt ───▶ │ Ollama · Gemma 4 (vision)│
 │ proof upload · verdict · XP   │ ◀── verdict ── │  judge + narrator lines  │
 └──────────────┬────────────────┘   (JSON)       └──────────────────────────┘
                │ verdict only (no photo)
                ▼
 ┌───────────────────────────────┐        ┌──────────────────────────────────┐
 │ FastAPI on Render             │ ─────▶ │ MongoDB Atlas                    │
 │  quest picker + dedupe        │        │ users · attempts · quests        │
 │  TabPFN: P(you finish quest)  │        │ + bge-m3 embeddings (Vector      │
 │  XP · streaks · badges        │        │   Search for near-duplicates)    │
 │  ElevenLabs narration (cached)│        │ + TTS audio cache                │
 └───────────────────────────────┘        └──────────────────────────────────┘
```

| Piece | What it does here |
|---|---|
| **Gemma 4** (via Ollama, local) | Looks at the proof photo and returns `{pass, confidence, seen, reaction}`; also writes the narrator line for each quest |
| **bge-m3** (via Ollama, local, one-off) | Embeds the quest pool so near-identical quests aren't served back to back |
| **TabPFN** | Predicts how likely *you* are to finish a quest right now (time, day, category, rarity, streak, your history). Low odds → up to 2× XP |
| **MongoDB Atlas** | All game data, plus **Atlas Vector Search** over quest embeddings |
| **Render** | Hosts the API and the website |
| **ElevenLabs** | Reads quests and Gemma's reactions aloud so you can keep your eyes off the screen |

## Run it locally

You need **Ollama**, **Python 3.12+** and **Node 20+**.

```bash
ollama pull gemma4:e2b      # the judge (any Gemma 4 vision tag works; e2b is the lightest)
ollama pull bge-m3          # only needed to regenerate quest embeddings
```

**API**

```bash
cd server
python -m venv .venv
.venv/Scripts/activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # all keys optional for local dev
uvicorn app.main:app --reload --port 8000
```

With no `MONGODB_URI` the API uses an in-memory database that is wiped on every restart, and seeds 300 **synthetic** attempt rows so the difficulty model has something to learn from.

**Website**

```bash
cd web
npm install
npm run dev                   # http://localhost:5173
```

## Using the hosted site with your Ollama

Ollama blocks requests from websites it doesn't know. Allow the Side Quests site once, then restart Ollama:

```powershell
setx OLLAMA_ORIGINS "https://<your-site>.onrender.com"     # Windows
```
```bash
launchctl setenv OLLAMA_ORIGINS "https://<your-site>.onrender.com"   # macOS
```

## Seeding Atlas

```bash
cd server
python -m scripts.seed embed       # (optional) re-embed quests with local bge-m3
python -m scripts.seed load        # upsert quests + create the vector search index
python -m scripts.seed synthetic   # 300 rows marked synthetic=True for TabPFN cold start
```

## Honesty notes

- **Synthetic data:** the TabPFN cold-start rows are generated and stored with `synthetic: true`. They're excluded from leaderboards and user stats. Real numbers in the write-up only come from real play.
- **Cold start:** a player needs 5 attempts before TabPFN replaces the starter heuristic. The quest card says which one produced your odds.
- **Trust:** the verdict is produced on the player's machine, so a determined cheater could fake it. That's the price of keeping photos private; it's a casual game.

## Commits after the deadline

None yet. Any commit after Oct 11, 2026 11:59 PM PDT will be listed here.
