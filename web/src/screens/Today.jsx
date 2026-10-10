import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, ArrowUp, Camera, Clock, CloudRain, Coins, Crosshair, Footprints, MapPin, RefreshCw, Sparkles, Sunset, Thermometer, Trophy, Wind } from "lucide-react";
import { api } from "../lib/api.js";
import { fileToBase64, judge, personalize } from "../lib/gemma.js";
import { departureLine, ranger, stopRanger } from "../lib/ranger.js";
import { bearingArrow, currentPlace, formatDistance } from "../lib/location.js";
import { CATEGORY_PHOTO, photo } from "../lib/photos.js";
import MapView from "../components/MapView.jsx";
import FieldCard from "../components/FieldCard.jsx";
import Topo from "../components/Topo.jsx";

const ACTIVE_KEY = "grassquest.active";
const SLOT_LABEL = { easy: "Easy win", sweet: "Sweet spot", stretch: "Stretch" };
const RARITY_COLOR = { common: "var(--common)", rare: "var(--rare)", legendary: "var(--legendary)" };

const loadActive = () => { try { return JSON.parse(localStorage.getItem(ACTIVE_KEY) || "null"); } catch { return null; } };
const saveActive = (a) => { try { a ? localStorage.setItem(ACTIVE_KEY, JSON.stringify(a)) : localStorage.removeItem(ACTIVE_KEY); } catch { /* ignore */ } };

export default function Today({ settings, model, player, onPlayer, onFocus, onPlace }) {
  const [data, setData] = useState(null); // { context, choices, rain_check }
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [brief, setBrief] = useState(null);
  const [active, setActive] = useState(loadActive); // { choice, brief, ctx, startedAt, stage }
  const [result, setResult] = useState(null);
  const [locMsg, setLocMsg] = useState("");

  async function relocate() {
    setLocMsg("Asking your browser for your exact location…");
    try {
      const p = await currentPlace();
      onPlace({ ...p, label: settings.place?.label });
      setLocMsg(`Updated · accurate to about ${p.accuracy} m`);
    } catch (e) {
      setLocMsg(e.message === "denied"
        ? "Location is blocked. Click the icon left of the address bar → Location → Allow, then try again."
        : "Couldn't get your location right now. You can also set it in Profile → change.");
    }
  }
  const briefs = useRef({}); // offer_id -> Promise<briefing>, so each one is written once
  const shown = useRef([]); // templates already offered this session, so rerolls bring genuinely new quests

  const briefingFor = useCallback((choice, ctx) => {
    if (!briefs.current[choice.offer_id]) {
      briefs.current[choice.offer_id] = personalize(settings.ollamaUrl, model, choice.quest, ctx)
        .catch(() => ({ title: choice.quest.title, briefing: "", tip: choice.quest.proof, failed: true }));
    }
    return briefs.current[choice.offer_id];
  }, [settings.ollamaUrl, model]);

  const load = useCallback(async (exclude = []) => {
    setLoading(true);
    setError("");
    setSelected(null);
    setBrief(null);
    try {
      const d = await api.today(settings.userId, settings.place, exclude);
      setData(d);
      if (d.rain_check && !exclude.length) ranger("rain-check");
      onPlayer(d.player);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [settings.userId, settings.place, onPlayer]);

  useEffect(() => { if (!active) load(); }, [settings.place?.lat, settings.place?.lon]); // eslint-disable-line react-hooks/exhaustive-deps

  // First visit to an area: nearby places are still being fetched, so refresh once they're likely ready
  useEffect(() => {
    if (!data?.context.places_loading || selected) return;
    const id = setTimeout(() => load(), 30000);
    return () => clearTimeout(id);
  }, [data, selected, load]);
  useEffect(() => { onFocus(active?.stage === "out"); }, [active?.stage, onFocus]);

  // Gemma pre-writes the sweet spot's briefing while the player is still reading the cards
  useEffect(() => {
    const sweet = data?.choices.find((c) => c.slot === "sweet");
    if (sweet && model) briefingFor(sweet, data.context);
  }, [data, model, briefingFor]);

  // ...and writes the briefing for whichever quest is selected
  useEffect(() => {
    if (!selected || !data || !model) return;
    let live = true;
    setBrief(null);
    briefingFor(selected, data.context).then((b) => live && setBrief(b));
    return () => { live = false; };
  }, [selected?.offer_id, model]); // eslint-disable-line react-hooks/exhaustive-deps

  function update(a) { setActive(a); saveActive(a); }

  async function go() {
    ranger(departureLine(data.context), selected.slot === "stretch" ? "stretch" : null);
    await api.accept(selected.offer_id).catch(() => {});
    update({ choice: selected, brief: brief ?? { title: selected.quest.title, briefing: "", tip: selected.quest.proof }, ctx: data.context, startedAt: Date.now(), stage: "out" });
  }

  function finish() {
    shown.current = [];
    update(null);
    setResult(null);
    load();
  }

  // ---------- reward reveal ----------
  if (result) return <Reveal result={result} onNext={finish} onRetry={() => { setResult(null); update({ ...active, stage: "proof" }); }} onGiveUp={() => { api.giveUp(active.choice.offer_id); finish(); }} />;

  // ---------- out in the world ----------
  if (active?.stage === "out") return <Expedition active={active} onBack={() => update({ ...active, stage: "proof" })} onCancel={() => { api.giveUp(active.choice.offer_id); finish(); }} />;
  if (active?.stage === "proof") {
    return (
      <Proof active={active} model={model} settings={settings}
        onBackOut={() => update({ ...active, stage: "out" })}
        onResult={(r) => {
          if (r.player) onPlayer(r.player);
          stopRanger();
          ranger(r.verdict, r.new_card ? "new-card" : null, r.level_up ? "level-up" : null, r.verdict !== "no" && r.player?.streak > 1 ? "streak" : null);
          setResult({ ...r, quest: active.brief.title || active.choice.quest.title });
        }} />
    );
  }

  // ---------- choose ----------
  const ctx = data?.context;
  return (
    <div className="wrap page">
      <div className="page-head">
        <div>
          <div className="kicker">{ctx ? [ctx.area.name, ctx.area.city].filter(Boolean).join(" · ") : "Today"}</div>
          <h1>Today's quests</h1>
        </div>
        <div style={{ display: "grid", gap: 8, justifyItems: "end" }}>
          {ctx && <Conditions ctx={ctx} />}
          <button className="btn link small" onClick={relocate}><Crosshair size={14} /> Update my location</button>
          {locMsg && <span className="small muted">{locMsg}</span>}
        </div>
      </div>

      {data?.rain_check && (
        <div className="card" style={{ marginBottom: 18, display: "flex", gap: 12, alignItems: "center", background: "var(--signal-soft)", boxShadow: "none" }}>
          <CloudRain /> <div><b>Rain check.</b> It's rough out there ({ctx.weather.label}). Here are quests you can do from a window or doorway, and your streak is safe: we've added a free freeze.</div>
        </div>
      )}

      {data?.context.places_loading && (
        <div className="pill" style={{ marginBottom: 14 }}><span className="spinner" style={{ width: 14, height: 14 }} /> First time here: mapping the parks, water and trails around you. Place quests will appear within a minute or two.</div>
      )}

      {error && <div className="card"><p className="error" style={{ marginTop: 0 }}>{error}</p><button className="btn" onClick={() => load()}><RefreshCw size={16} /> Try again</button></div>}

      <div className="grid-today">
        <div>
          <div className="choices">
            {loading && [0, 1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 130 }} />)}
            {!loading && data?.choices.map((c) => (
              <button key={c.offer_id} className="choice" aria-pressed={selected?.offer_id === c.offer_id} onClick={() => setSelected(c)}>
                <img src={photo(CATEGORY_PHOTO[c.quest.cat], 300)} alt="" />
                <div className="choice-body">
                  <div className="choice-top">
                    <span className={`slot ${c.slot}`}>{SLOT_LABEL[c.slot]}</span>
                    <span className="rarity" style={{ "--r-color": RARITY_COLOR[c.quest.rarity] }}>{c.quest.rarity}</span>
                  </div>
                  <h3>{c.quest.title}</h3>
                  <div className="meta">
                    <span><Clock size={14} /> ~{c.minutes} min</span>
                    {c.quest.place && <span><MapPin size={14} /> {formatDistance(c.quest.place.dist_m)} {c.quest.place.bearing}</span>}
                    <span><Trophy size={14} /> +{c.xp} XP</span>
                    <span><Coins size={14} /> +{c.seeds}</span>
                  </div>
                  <div className="odds" title={`${Math.round(c.p * 100)}% chance you'll finish`}><div style={{ width: `${c.p * 100}%` }} /></div>
                </div>
              </button>
            ))}
          </div>
          {!loading && data && (
            <div className="actions" style={{ marginTop: 14 }}>
              <button className="btn quiet" onClick={() => { shown.current = [...shown.current, ...data.choices.map((c) => c.quest.template_id)].slice(-15); load(shown.current); }}><RefreshCw size={16} /> Three different quests</button>
              <span className="small muted">{data.choices[0]?.source === "tabpfn" ? "Odds and minutes predicted by TabPFN" : "Odds are a starter estimate"}</span>
            </div>
          )}
        </div>

        <div>
          {!selected && ctx && (
            <div className="card briefing">
              <MapView center={settings.place} />
              <div className="briefing-body">
                <div className="kicker">Within walking distance</div>
                <div className="meta" style={{ marginTop: 8 }}>
                  {Object.entries(ctx.places).slice(0, 8).map(([k, p]) => <span key={k}><MapPin size={14} /> {p.name || k} · {formatDistance(p.dist_m)}</span>)}
                  {!Object.keys(ctx.places).length && <span>No mapped parks or water nearby, so it's street and sky quests today.</span>}
                </div>
                <p className="small muted" style={{ marginBottom: 0 }}>Pick a quest to get your briefing.</p>
              </div>
            </div>
          )}
          {selected && (
            <Briefing choice={selected} brief={brief} ctx={ctx} place={settings.place} model={model} onGo={go} />
          )}
        </div>
      </div>
    </div>
  );
}

function Conditions({ ctx }) {
  const w = ctx.weather;
  const s = ctx.sun;
  return (
    <div className="conditions">
      <span className="pill"><Thermometer size={15} /> {w.temp}°C · {w.label}</span>
      {w.wind >= 20 && <span className="pill"><Wind size={15} /> {w.wind} km/h</span>}
      {s.phase !== "night" && s.minutes_to_sunset > 0 && <span className="pill"><Sunset size={15} /> sunset in {s.minutes_to_sunset >= 120 ? `${Math.round(s.minutes_to_sunset / 60)} h` : `${s.minutes_to_sunset} min`}</span>}
      {s.phase === "night" && <span className="pill">Night</span>}
      {w.rain_soon_at && <span className="pill warn"><CloudRain size={15} /> rain around {w.rain_soon_at.slice(11, 16)}</span>}
    </div>
  );
}

function Briefing({ choice, brief, ctx, place, model, onGo }) {
  const q = choice.quest;
  return (
    <div className="card briefing">
      <MapView center={place} destination={q.place} />
      <div className="briefing-body">
        <span className={`slot ${choice.slot}`}>{SLOT_LABEL[choice.slot]}</span>
        <h2>{brief?.title || q.title}</h2>
        <div className="ranger">
          <div className="ranger-badge"><Sparkles size={18} /></div>
          {brief ? <p>{brief.briefing || "Your quest is set. Head out and bring back proof."}</p>
            : <div style={{ flex: 1 }}><div className="skeleton" style={{ height: 14, marginBottom: 8 }} /><div className="skeleton" style={{ height: 14, width: "70%" }} /><p className="small muted" style={{ marginTop: 8 }}>{model ? `${model} is writing your briefing…` : "Briefing needs your local Gemma."}</p></div>}
        </div>
        {brief?.tip && <p className="small"><Camera size={14} style={{ verticalAlign: -2 }} /> <b>Proof:</b> {brief.tip}</p>}
        <div className="reward-row">
          <span className="reward-chip"><Trophy size={16} /> +{choice.xp} XP</span>
          <span className="reward-chip"><Coins size={16} /> +{choice.seeds} Seeds</span>
          <span className="reward-chip"><Clock size={16} /> ~{choice.minutes} min</span>
        </div>
        <p className="why">
          {Math.round(choice.p * 100)}% chance you'll finish this right now, so XP ×{choice.xp_multiplier}
          {choice.seed_multiplier > 1 && <>, and your streak gives Seeds ×{choice.seed_multiplier}</>}.
          {choice.source === "tabpfn" ? " Predicted by TabPFN from weather, time, distance and play history." : ""}
        </p>
        <button className="btn primary big" onClick={onGo} style={{ width: "100%" }}><Footprints size={18} /> Start expedition</button>
      </div>
    </div>
  );
}

function Expedition({ active, onBack, onCancel }) {
  const [, tick] = useState(0);
  useEffect(() => { const id = setInterval(() => tick((n) => n + 1), 1000); return () => clearInterval(id); }, []);
  const s = Math.floor((Date.now() - active.startedAt) / 1000);
  const q = active.choice.quest;
  return (
    <div className="expedition">
      <Topo seed={42} rings={18} />
      <div className="expedition-in">
        <div className="kicker" style={{ color: "#a89f8e" }}>Expedition in progress</div>
        <h1>Screen off.<br />Go.</h1>
        <p className="quest-line">{active.brief.title || q.title}</p>
        {q.place && (
          <div className="compass">
            <ArrowUp size={22} style={{ transform: `rotate(${bearingArrow(q.place.bearing)}deg)` }} />
            {q.place.name} · {formatDistance(q.place.dist_m)} {q.place.bearing}
          </div>
        )}
        {active.brief.briefing && <p style={{ color: "#c9c0af", maxWidth: "48ch", margin: "8px auto" }}>{active.brief.briefing}</p>}
        <div className="timer">{Math.floor(s / 60)}:{String(s % 60).padStart(2, "0")}</div>
        <div className="actions" style={{ justifyContent: "center" }}>
          <button className="btn primary big" onClick={onBack}><Camera size={18} /> I'm back with proof</button>
          <button className="btn" onClick={onCancel}>Abandon</button>
        </div>
        <p className="small" style={{ color: "#8a8172", marginTop: 26 }}>Close the laptop. Take photos on your phone, then share them to this computer.</p>
      </div>
    </div>
  );
}

function Proof({ active, model, settings, onBackOut, onResult }) {
  const [file, setFile] = useState(null);
  const [over, setOver] = useState(false);
  const [stage, setStage] = useState("pick");
  const [error, setError] = useState("");
  const q = active.choice.quest;
  const url = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => () => url && URL.revokeObjectURL(url), [url]);

  async function submit() {
    setStage("judging");
    setError("");
    try {
      const b64 = await fileToBase64(file);
      const v = await judge(settings.ollamaUrl, model, { ...q, title: active.brief.title || q.title }, b64);
      const res = await api.verdict(active.choice.offer_id, v);
      onResult({ ...res, judged: v });
    } catch (e) {
      setError(e.message.includes("fetch") ? "Couldn't reach your local Gemma. Is Ollama still running?" : e.message);
      setStage("pick");
    }
  }

  const pick = (f) => f && f.type.startsWith("image/") && setFile(f);

  return (
    <div className="wrap page" style={{ maxWidth: 760 }}>
      <button className="btn link" onClick={onBackOut}><ArrowLeft size={16} /> Back to expedition</button>
      <div className="kicker" style={{ marginTop: 12 }}>Show your proof</div>
      <h1 style={{ fontSize: "clamp(2rem,5vw,3rem)", textTransform: "uppercase", margin: "6px 0 18px" }}>{active.brief.title || q.title}</h1>
      <div className="card">
        {!file ? (
          <label className={`drop${over ? " over" : ""}`} onDragOver={(e) => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)}
            onDrop={(e) => { e.preventDefault(); setOver(false); pick(e.dataTransfer.files?.[0]); }}>
            <input type="file" accept="image/*" onChange={(e) => pick(e.target.files?.[0])} />
            <Camera size={36} />
            <b>Drop your photo here, or click to choose</b>
            <span className="small muted">{active.brief.tip || q.proof}</span>
          </label>
        ) : (
          <>
            <img className="photo" src={url} alt="Your proof" />
            {stage === "judging" ? (
              <div className="judging"><span className="spinner" /> {model} is looking at your photo, on this computer…</div>
            ) : (
              <div className="actions" style={{ marginTop: 14 }}>
                <button className="btn primary big" onClick={submit}>Judge it</button>
                <button className="btn quiet" onClick={() => setFile(null)}>Different photo</button>
              </div>
            )}
          </>
        )}
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}

function Reveal({ result, onNext, onRetry, onGiveUp }) {
  const v = result.judged;
  const won = result.verdict !== "no";
  return (
    <div className="wrap page" style={{ maxWidth: 820 }}>
      <div className="card reveal topo-host">
        <Topo seed={result.xp || 3} />
        <div style={{ position: "relative" }}>
          <span className={`verdict-tag tag-${result.verdict}`}>{result.verdict === "pass" ? "Quest complete" : result.verdict === "close" ? "Close enough" : "Not yet"}</span>
          <h1 className="pop">{won ? (result.verdict === "pass" ? "Nailed it." : "Half credit!") : "So close."}</h1>
          <p className="reaction">“{v.reaction}”</p>
          <p className="small muted">Gemma saw: {v.seen} · {(v.ms / 1000).toFixed(1)} s on your computer</p>
          {won && (
            <div className="gains">
              <div className="gain pop"><b>+{result.xp}</b><span>XP</span></div>
              <div className="gain pop" style={{ animationDelay: ".1s" }}><b>+{result.seeds + result.card_seeds}</b><span>Seeds</span></div>
            </div>
          )}
          {result.level_up && <p className="pop"><b>Level up!</b> You're now <b>{result.player.title}</b> (level {result.player.level}).</p>}
          {result.new_card && (
            <div style={{ maxWidth: 280, margin: "18px auto", textAlign: "left" }}>
              <div className="kicker" style={{ textAlign: "center", marginBottom: 8 }}>New Field Guide card · +{result.card_seeds} Seeds</div>
              <FieldCard card={result.new_card} flip />
            </div>
          )}
          {result.new_badges?.length > 0 && (
            <div className="badges" style={{ maxWidth: 520, margin: "16px auto" }}>
              {result.new_badges.map((b) => <div className="badge pop" key={b.key}><div className="ic">{b.icon}</div><b>{b.name}</b><span>{b.description}</span></div>)}
            </div>
          )}
          <div className="actions" style={{ justifyContent: "center", marginTop: 20 }}>
            {won ? <button className="btn primary big" onClick={onNext}>Next quest</button> : (
              <>
                <button className="btn primary big" onClick={onRetry}>Try another photo</button>
                <button className="btn quiet" onClick={onGiveUp}>Give up</button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
