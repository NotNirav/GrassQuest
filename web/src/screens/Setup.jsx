import { useCallback, useEffect, useState } from "react";
import { Check, Cpu, MapPin, RefreshCw, User, X } from "lucide-react";
import { api } from "../lib/api.js";
import { currentPlace, locationPermission, round } from "../lib/location.js";
import MapView from "../components/MapView.jsx";
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

  // Ask for the browser's location as soon as setup opens (this is what shows the permission popup)
  useEffect(() => {
    if (place) return;
    locationPermission().then((state) => {
      if (state === "denied") setPlaceErr("denied");
      else locate();
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Suggestions while typing: localities, streets, buildings, landmarks near you
  useEffect(() => {
    if (query.trim().length < 3) { setResults([]); return; }
    const id = setTimeout(() => {
      api.geocode(query.trim(), place || settings.place).then(setResults).catch(() => {});
    }, 300);
    return () => clearTimeout(id);
  }, [query]); // eslint-disable-line react-hooks/exhaustive-deps

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
      await choose(p);
    } catch (e) {
      setPlaceErr(e.message === "denied" || e.message === "timeout" || e.message === "unavailable" ? e.message : e.message);
    } finally {
      setLocating(false);
    }
  }

  // Looks up the area name and starts mapping nearby places in the background
  async function choose(p) {
    const ctx = await api.context(p.lat, p.lon);
    setPlace({ ...p, label: [ctx.area.name, ctx.area.city].filter(Boolean).join(", ") || "Your area" });
  }

  async function search(e) {
    e.preventDefault();
    setPlaceErr("");
    try {
      const r = await api.geocode(query, place || settings.place);
      setResults(r);
      if (!r.length) setPlaceErr("Nothing found. Try your locality, a road, or a landmark near you.");
    } catch (e2) {
      setPlaceErr(e2.message);
    }
  }

  const LOCATION_HELP = {
    denied: <>Location is blocked for this site. Click the <b>lock / tune icon</b> left of the address bar → <b>Location → Allow</b>, then reload. On Windows also check <b>Settings → Privacy &amp; security → Location</b> is on and your browser is allowed.</>,
    timeout: "Your computer took too long to find its location. Try again, or search below.",
    unavailable: "Your computer couldn't work out where it is. Make sure Windows location is on, or search below.",
  };

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
            <>
              <p className="muted" style={{ margin: "0 0 10px" }}>
                {place.label}{place.accuracy ? ` · accurate to about ${place.accuracy} m` : ""} <button className="btn link" onClick={() => setPlace(null)}>change</button>
              </p>
              <div style={{ borderRadius: 12, overflow: "hidden", border: "1px solid var(--line)" }}>
                <MapView center={place} zoom={16} onPick={(p) => setPlace((cur) => ({ ...cur, lat: round(p.lat), lon: round(p.lon), accuracy: null, moved: true }))} />
              </div>
              <p className="small muted" style={{ margin: "8px 0 0" }}>Not quite right? Tap the map where you actually are.{place.moved ? " Pin moved." : ""}</p>
            </>
          ) : (
            <>
              <p className="muted" style={{ margin: "0 0 10px" }}>Used for live weather and the real places near you. Your exact spot is only used to measure distances and is never stored.</p>
              <button className="btn dark" onClick={locate} disabled={locating}>{locating ? "Asking your browser…" : "Use my exact location"}</button>
              {placeErr && <div className="error">{LOCATION_HELP[placeErr] ?? placeErr}</div>}
              <form onSubmit={search} className="field" style={{ marginTop: 14 }}>
                <label className="small muted" htmlFor="city">Or search your locality, road, building or a landmark</label>
                <div style={{ display: "flex", gap: 8 }}>
                  <input id="city" className="input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. Pimple Saudagar, Spine Road, Phoenix Mall" autoComplete="off" />
                  <button className="btn quiet">Search</button>
                </div>
              </form>
              {results.length > 0 && (
                <div className="results">
                  {results.map((r) => (
                    <button key={`${r.lat},${r.lon}`} onClick={() => { setResults([]); setQuery(""); choose({ lat: r.lat, lon: r.lon }).catch((e2) => setPlaceErr(e2.message)); }}>
                      <b>{r.title}</b>{r.detail && <span className="muted"> · {r.detail}</span>}
                    </button>
                  ))}
                </div>
              )}
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
