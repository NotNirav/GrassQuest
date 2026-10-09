import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api.js";
import { fileToBase64, judgePhoto, questIntro } from "../lib/gemma.js";
import { speak, stop } from "../lib/voice.js";

const RARITY_COLOR = { common: "var(--common)", rare: "var(--rare)", legendary: "var(--legendary)", boss: "var(--boss)" };
const CATEGORY_ICON = { plants: "🌿", birds: "🐦", sky: "☁️", walking: "🥾", water: "💧", textures: "🪨", social: "🧺" };

export default function QuestFlow({ settings, player, onPlayer, onFocus }) {
  const [stage, setStage] = useState("loading"); // loading | offer | outside | proof | judging | result
  const [offer, setOffer] = useState(null);
  const [boss, setBoss] = useState(null);
  const [intro, setIntro] = useState("");
  const [error, setError] = useState("");
  const [outsideSince, setOutsideSince] = useState(null);
  const [photo, setPhoto] = useState(null); // { file, url }
  const [verdict, setVerdict] = useState(null);
  const [reward, setReward] = useState(null);
  const skipped = useRef([]);
  const currentOffer = useRef(null);

  // Gemma writes the narrator line locally. Ignore answers for quests the player already moved past.
  const fetchIntro = useCallback((o) => {
    currentOffer.current = o.offer_id;
    setIntro("");
    questIntro(settings.ollamaUrl, settings.model, o.quest)
      .then((text) => currentOffer.current === o.offer_id && setIntro(text))
      .catch(() => {});
  }, [settings.ollamaUrl, settings.model]);

  const narrate = useCallback((text) => settings.voice && speak(text), [settings.voice]);

  const loadQuest = useCallback(async ({ isBoss = false } = {}) => {
    setStage("loading");
    setError("");
    setIntro("");
    try {
      const o = await api.nextQuest(settings.userId, { exclude: skipped.current, boss: isBoss });
      if (o.boss_done) {
        setBoss(o);
        return loadQuest();
      }
      setOffer(o);
      setStage("offer");
      fetchIntro(o);
    } catch (e) {
      setError(e.message);
      setStage("offer");
    }
  }, [settings.userId, fetchIntro]);

  useEffect(() => {
    loadQuest();
    api.nextQuest(settings.userId, { boss: true }).then(setBoss).catch(() => {});
    return stop;
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    onFocus(stage === "outside");
  }, [stage, onFocus]);

  async function reroll() {
    if (offer) {
      skipped.current = [...skipped.current, offer.quest._id].slice(-10);
      api.giveUp(offer.offer_id).catch(() => {});
    }
    loadQuest();
  }

  function takeBoss() {
    if (!boss || boss.boss_done) return;
    if (offer && offer.quest.rarity !== "boss") api.giveUp(offer.offer_id).catch(() => {});
    setOffer(boss);
    setStage("offer");
    fetchIntro(boss);
  }

  function goOutside() {
    narrate(intro || `Your quest: ${offer.quest.title}. Now put the screen down and go.`);
    setOutsideSince(Date.now());
    setStage("outside");
  }

  function pickPhoto(file) {
    if (!file || !file.type.startsWith("image/")) return;
    if (photo) URL.revokeObjectURL(photo.url);
    setPhoto({ file, url: URL.createObjectURL(file) });
    setVerdict(null);
    setError("");
  }

  async function judge() {
    setStage("judging");
    setError("");
    try {
      const b64 = await fileToBase64(photo.file);
      const v = await judgePhoto(settings.ollamaUrl, settings.model, offer.quest, b64);
      setVerdict(v);
      const res = await api.verdict(offer.offer_id, v);
      setReward(res);
      if (res.player) onPlayer(res.player);
      setStage("result");
      narrate(v.reaction);
    } catch (e) {
      setError(e.message.includes("fetch") ? "Couldn't reach Ollama. Is it still running?" : e.message);
      setStage("proof");
    }
  }

  async function next() {
    if (photo) URL.revokeObjectURL(photo.url);
    setPhoto(null);
    setVerdict(null);
    setReward(null);
    skipped.current = [];
    if (offer?.quest.rarity === "boss") api.nextQuest(settings.userId, { boss: true }).then(setBoss).catch(() => {});
    loadQuest();
  }

  // ---------- outside: almost nothing on screen ----------
  if (stage === "outside") {
    return (
      <section className="outside">
        <div>
          <div className="leaf-spin">🌿</div>
          <h1>Go. Touch grass.</h1>
          <p className="quest-title">{offer.quest.title}</p>
          <Timer since={outsideSince} />
          <div className="actions" style={{ justifyContent: "center" }}>
            <button className="btn primary big" onClick={() => setStage("proof")}>I'm back with proof 📸</button>
            <button className="btn ghost" onClick={() => setStage("offer")}>Not yet</button>
          </div>
          <p className="muted small" style={{ marginTop: 28 }}>Close the laptop. This page will wait for you.</p>
        </div>
      </section>
    );
  }

  // ---------- result ----------
  if (stage === "result" && verdict) {
    const passed = reward?.passed;
    return (
      <section className="card result">
        <div className="result-emoji">{passed ? "🏆" : "🤔"}</div>
        <h1>{passed ? "Quest complete!" : "Not quite…"}</h1>
        {passed && <div className="gain">+{reward.xp} XP</div>}
        {passed && reward.level_up && <p><b>Level up!</b> You're now level {reward.player.level}: {reward.player.title}.</p>}
        <p className="reaction">“{verdict.reaction}”</p>
        <p className="seen">Gemma saw: {verdict.seen} · {Math.round(verdict.confidence * 100)}% sure · {(verdict.ms / 1000).toFixed(1)}s on your machine</p>
        {passed && reward.new_badges.length > 0 && (
          <div className="badge-row">
            {reward.new_badges.map((b) => (
              <div className="badge" key={b.key}><div className="icon">{b.icon}</div><div className="name">{b.name}</div><div className="desc">{b.description}</div></div>
            ))}
          </div>
        )}
        <div className="actions" style={{ justifyContent: "center" }}>
          {passed ? (
            <button className="btn primary big" onClick={next}>Next quest →</button>
          ) : (
            <>
              <button className="btn primary big" onClick={() => { setPhoto(null); setStage("outside"); setOutsideSince(Date.now()); }}>Try again outside</button>
              <button className="btn ghost" onClick={() => setStage("proof")}>Use a different photo</button>
              <button className="btn danger" onClick={() => { api.giveUp(offer.offer_id).catch(() => {}); next(); }}>Give up</button>
            </>
          )}
        </div>
      </section>
    );
  }

  const q = offer?.quest;
  return (
    <div className="grid">
      <div className="stack">
        {(stage === "proof" || stage === "judging") && q ? (
          <ProofCard quest={q} photo={photo} stage={stage} onPick={pickPhoto} onJudge={judge} onBack={() => setStage("offer")} error={error} model={settings.model} />
        ) : (
          <QuestCard offer={offer} intro={intro} loading={stage === "loading"} error={error}
            onGo={goOutside} onReroll={reroll} onListen={() => narrate(intro || `Your quest: ${q?.title}`)} onRetry={() => loadQuest()} />
        )}
      </div>
      <aside className="stack">
        <BossCard boss={boss} active={q?.rarity === "boss"} onTake={takeBoss} />
        <section className="card">
          <h2>How it works</h2>
          <ol className="steps small">
            <li>Get a quest. Hit <b>I'm heading out</b>.</li>
            <li>Leave the screen behind and go do it.</li>
            <li>Come back with a photo. <b>Gemma, running on your own computer</b>, judges it. The photo never leaves your machine.</li>
            <li>Earn XP. Quests that are hard <i>for you</i> pay more.</li>
          </ol>
        </section>
      </aside>
    </div>
  );
}

function QuestCard({ offer, intro, loading, error, onGo, onReroll, onListen, onRetry }) {
  if (error && !offer) {
    return (
      <section className="card">
        <h2>Couldn't load a quest</h2>
        <p className="error">{error}</p>
        <button className="btn" onClick={onRetry}>Try again</button>
      </section>
    );
  }
  if (loading || !offer) {
    return <section className="card quest"><div className="judging"><Dots /> Finding you a quest…</div></section>;
  }
  const q = offer.quest;
  const pct = Math.round(offer.p_complete * 100);
  return (
    <section className="card quest" style={{ "--rarity": RARITY_COLOR[q.rarity] }}>
      <div className="quest-kicker">
        <span className="chip rarity">{q.rarity === "boss" ? "👑 weekly boss" : q.rarity}</span>
        <span className="chip">{CATEGORY_ICON[q.category]} {q.category}</span>
      </div>
      <h1 className="quest-title">{q.title}</h1>
      <p className="quest-intro">{intro || " "}</p>
      <div className="reward">
        <div className="reward-xp">+{offer.xp} XP</div>
        <div className="reward-why">
          We think you've got a <b>{pct}%</b> chance of doing this right now → <b>×{offer.multiplier}</b> XP
          {offer.streak_bonus > 0 && <> · streak bonus <b>+{Math.round(offer.streak_bonus * 100)}%</b></>}
          <br />
          <span className="small">Odds by {offer.p_source === "tabpfn" ? "TabPFN, from everyone's play history" : "a starter estimate (TabPFN takes over after 5 quests)"}</span>
        </div>
      </div>
      <div className="actions">
        <button className="btn primary big" onClick={onGo}>I'm heading out →</button>
        <button className="btn ghost" onClick={onListen} title="Read the quest aloud">🎧 Read it to me</button>
        {q.rarity !== "boss" && <button className="btn ghost" onClick={onReroll}>Different quest</button>}
      </div>
      {error && <p className="error">{error}</p>}
    </section>
  );
}

function ProofCard({ quest, photo, stage, onPick, onJudge, onBack, error, model }) {
  const [over, setOver] = useState(false);
  return (
    <section className="card">
      <h2>Show your proof</h2>
      <p className="muted" style={{ marginTop: -6 }}>{quest.title}</p>
      {!photo ? (
        <label className={`drop${over ? " over" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setOver(true); }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => { e.preventDefault(); setOver(false); onPick(e.dataTransfer.files?.[0]); }}>
          <input type="file" accept="image/*" capture="environment" onChange={(e) => onPick(e.target.files?.[0])} />
          <div className="drop-icon">📸</div>
          <b>Drop your photo here</b> or click to choose
          <div className="small muted">Move it from your phone however you like. It stays on this computer.</div>
        </label>
      ) : (
        <>
          <img className="photo" src={photo.url} alt="Your proof" />
          {stage === "judging" ? (
            <div className="judging"><Dots /> {model} is squinting at your photo…</div>
          ) : (
            <div className="actions" style={{ marginTop: 14 }}>
              <button className="btn primary big" onClick={onJudge}>Judge it ⚖️</button>
              <label className="btn ghost" style={{ display: "inline-flex", alignItems: "center" }}>
                Change photo
                <input type="file" accept="image/*" hidden onChange={(e) => onPick(e.target.files?.[0])} />
              </label>
            </div>
          )}
        </>
      )}
      {error && <p className="error">{error}</p>}
      {stage !== "judging" && <button className="btn ghost" style={{ marginTop: 14 }} onClick={onBack}>← Back to quest</button>}
    </section>
  );
}

function BossCard({ boss, active, onTake }) {
  if (!boss) return null;
  return (
    <section className="card boss">
      <span className="chip rarity">👑 Weekly boss</span>
      <h3>{boss.quest.title}</h3>
      {boss.boss_done ? (
        <p className="muted small">Defeated this week. A new boss appears on Monday.</p>
      ) : (
        <>
          <p className="muted small">Big outdoor challenge, worth <b>+{boss.xp} XP</b>. One per week.</p>
          <button className="btn" disabled={active} onClick={onTake}>{active ? "Boss quest active" : "Take on the boss"}</button>
        </>
      )}
    </section>
  );
}

function Timer({ since }) {
  const [, tick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => tick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const s = Math.floor((Date.now() - since) / 1000);
  return <div className="timer">Outside for {Math.floor(s / 60)}:{String(s % 60).padStart(2, "0")}</div>;
}

function Dots() {
  return <span className="dots" aria-hidden="true"><span /><span /><span /></span>;
}
