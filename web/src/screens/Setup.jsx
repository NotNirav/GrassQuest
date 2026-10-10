import { useCallback, useEffect, useState } from "react";
import { Check, Cpu, MapPin, RefreshCw, User, X } from "lucide-react";
import { api } from "../lib/api.js";
import { currentPlace } from "../lib/location.js";
import { detectGemma, MIN_MODEL } from "../lib/gemma.js";

export default function Setup({ settings, existing = false, onDone }) {
  const [place, setPlace] = useState(settings.place);
  const [placeErr, setPlaceErr] = useState("");
  const [locating, setLocating] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [ai, setAi] = useState({ status: "checking" });
  const [handle, setHandle] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const checkAi = useCallback(async () => {
    setAi({ status: "checking" });
    setAi(await detectGemma(settings.ollamaUrl));
  }, [settings.ollamaUrl]);
  useEffect(() => { checkAi(); }, [checkAi]);

  async function locate() {
    setLocating(true);
    setPlaceErr("");
    try {
      const p = await currentPlace();
      const ctx = await api.context(p.lat, p.lon);
      setPlace({ ...p, label: [ctx.area.name, ctx.area.city].filter(Boolean).join(", ") || "Your area" });
    } catch (e) {
      setPlaceErr(e.message);
    } finally {
      setLocating(false);
    }
  }

  async function search(e) {
    e.preventDefault();
    setPlaceErr("");
    try {
      const r = await api.geocode(query);
      setResults(r);
      if (!r.length) setPlaceErr("No places found. Try a city name.");
    } catch (e2) {
      setPlaceErr(e2.message);
    }
  }

  async function start(e) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      if (existing) return onDone(null, { place });
      const user = await api.createUser(handle.trim());
      onDone(user, { place });
    } catch (e2) {
      setErr(e2.message);
    } finally {
      setBusy(false);
    }
  }

  const nameOk = existing || handle.trim().length >= 2;
  const ready = place && ai.status === "ok" && nameOk;

  return (
    <div className="wrap setup">
      <div className="kicker">Before you head out</div>
      <h1 style={{ fontSize: "clamp(2.4rem,6vw,4rem)", textTransform: "uppercase", margin: "6px 0 24px" }}>Three quick checks</h1>

      <section className={`check ${place ? "ok" : ""}`}>
        <div className="check-dot">{place ? <Check /> : <MapPin />}</div>
        <div>
          <h3>Where you are</h3>
          {place ? (
            <p className="muted" style={{ margin: 0 }}>{place.label} <button className="btn link" onClick={() => setPlace(null)}>change</button></p>
          ) : (
            <>
              <p className="muted" style={{ margin: "0 0 10px" }}>Used for live weather and the real places near you. Rounded to about 1 km, never stored raw.</p>
              <button className="btn dark" onClick={locate} disabled={locating}>{locating ? "Finding you…" : "Use my location"}</button>
              <form onSubmit={search} className="field" style={{ marginTop: 14 }}>
                <label className="small muted" htmlFor="city">Or search for your town</label>
                <div style={{ display: "flex", gap: 8 }}>
                  <input id="city" className="input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. Pune" />
                  <button className="btn quiet">Search</button>
                </div>
              </form>
              {results.length > 0 && (
                <div className="results">
                  {results.map((r) => (
                    <button key={r.label} onClick={() => { setPlace({ lat: r.lat, lon: r.lon, label: r.label.split(",").slice(0, 2).join(",") }); setResults([]); }}>{r.label}</button>
                  ))}
                </div>
              )}
              {placeErr && <div className="error">{placeErr}</div>}
            </>
          )}
        </div>
      </section>

      <section className={`check ${ai.status === "ok" ? "ok" : ai.status === "checking" ? "" : "bad"}`}>
        <div className="check-dot">{ai.status === "ok" ? <Check /> : ai.status === "checking" ? <Cpu /> : <X />}</div>
        <div>
          <h3>Your local AI judge</h3>
          {ai.status === "checking" && <p className="muted" style={{ margin: 0 }}>Looking for Gemma on this computer…</p>}
          {ai.status === "ok" && <p className="muted" style={{ margin: 0 }}>Found <b>{ai.model}</b>. Your photos stay on this computer.</p>}
          {ai.status === "missing" && (
            <>
              <p className="muted" style={{ margin: 0 }}>Ollama is running, but there's no Gemma 4 model yet. Run this once (about 7 GB):</p>
              <div className="code">ollama pull {MIN_MODEL}</div>
            </>
          )}
          {(ai.status === "offline" || ai.status === "blocked") && (
            <p className="muted" style={{ margin: 0 }}>
              {ai.status === "offline" ? <>Ollama isn't running. Install it from <a href="https://ollama.com/download" target="_blank" rel="noreferrer">ollama.com</a> and open it.</>
                : "Ollama is running but blocked this site. See the FAQ: “It says Ollama is blocked”."}
            </p>
          )}
          {ai.status !== "ok" && ai.status !== "checking" && <button className="btn quiet" style={{ marginTop: 10 }} onClick={checkAi}><RefreshCw size={16} /> Check again</button>}
        </div>
      </section>

      <form className={`check ${nameOk ? "ok" : ""}`} onSubmit={start}>
        <div className="check-dot">{nameOk ? <Check /> : <User />}</div>
        <div>
          <h3>Your explorer name</h3>
          {existing ? <p className="muted" style={{ margin: 0 }}>You're already signed in.</p>
            : <input className="input" value={handle} onChange={(e) => setHandle(e.target.value)} placeholder="e.g. MossBoss" maxLength={24} aria-label="Explorer name" />}
          <div style={{ marginTop: 16 }}>
            <button className="btn primary big" disabled={!ready || busy}>{busy ? "Setting up camp…" : "Show me today's quests"}</button>
          </div>
          {!ready && <p className="small muted" style={{ marginTop: 8 }}>All three checks need to be green.</p>}
          {err && <div className="error">{err}</div>}
        </div>
      </form>
    </div>
  );
}
