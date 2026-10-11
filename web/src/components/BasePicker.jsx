import { useCallback, useEffect, useRef, useState } from "react";
import { Crosshair, Lock, MapPin, Search } from "lucide-react";
import { api } from "../lib/api.js";
import { round } from "../lib/location.js";
import MapView from "./MapView.jsx";

const INDIA = { lat: 20.6, lon: 78.9 };

/**
 * Set your base camp: search a building / society / road / landmark, fly in, drag or tap the pin onto your
 * exact building (satellite helps), confirm the address, lock. Nothing is guessed silently.
 */
export default function BasePicker({ initial, onLock, onCancel }) {
  const [pin, setPin] = useState(initial ? { lat: initial.lat, lon: initial.lon } : null);
  const [view, setView] = useState(initial ?? INDIA);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [addr, setAddr] = useState(initial?.label ? { title: initial.label, detail: "" } : null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const reqId = useRef(0);
  const picked = useRef(""); // the text of a chosen result: don't search it again

  // suggestions while typing, near the current map view
  useEffect(() => {
    if (query.trim().length < 3 || query === picked.current) { setResults([]); return; }
    const id = setTimeout(() => {
      api.geocode(query.trim(), pin ?? (view === INDIA ? null : view)).then(setResults).catch(() => setResults([]));
    }, 280);
    return () => clearTimeout(id);
  }, [query]); // eslint-disable-line react-hooks/exhaustive-deps

  // confirm what's under the pin
  useEffect(() => {
    if (!pin) return;
    const id = ++reqId.current;
    setAddr(null);
    api.reverse(pin.lat, pin.lon).then((a) => id === reqId.current && setAddr(a)).catch(() => {});
  }, [pin?.lat, pin?.lon]); // eslint-disable-line react-hooks/exhaustive-deps

  const pick = useCallback((p) => { setPin({ lat: round(p.lat), lon: round(p.lon) }); setNote(""); }, []);

  function choose(r) {
    setResults([]);
    picked.current = r.title;
    setQuery(r.title);
    const p = { lat: r.lat, lon: r.lon };
    setPin(p);
    setView(p);
    setNote("Zoomed in. Drag the orange pin onto your exact building. Satellite view helps.");
  }

  // optional starting point: listen for up to 10 s and keep the most accurate fix (browsers refine over time)
  function useDevice() {
    if (!("geolocation" in navigator)) return setNote("This browser can't share location. Search instead.");
    setBusy(true);
    setNote("Asking your browser…");
    let best = null;
    const stop = (msg) => { navigator.geolocation.clearWatch(watch); setBusy(false); if (msg) setNote(msg); };
    const watch = navigator.geolocation.watchPosition(
      (pos) => {
        if (!best || pos.coords.accuracy < best.coords.accuracy) {
          best = pos;
          const p = { lat: round(pos.coords.latitude), lon: round(pos.coords.longitude) };
          setPin(p);
          setView(p);
          setNote(`Your browser thinks you're here, give or take ${Math.round(pos.coords.accuracy)} m…`);
        }
        if (pos.coords.accuracy <= 30) stop(`Found you to within ${Math.round(pos.coords.accuracy)} m. Check the pin is on your building, then lock it.`);
      },
      (err) => stop(err.code === 1
        ? "Location is blocked for this site (icon left of the address bar → Location → Allow). Or just search your building."
        : "Your browser couldn't find you. Search your building or road instead."),
      { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 },
    );
    setTimeout(() => {
      if (!best) return;
      const acc = Math.round(best.coords.accuracy);
      stop(acc > 300
        ? `Your browser only knows roughly where you are (±${acc >= 1000 ? `${(acc / 1000).toFixed(1)} km` : `${acc} m`}). Search your building, or drag the pin to it.`
        : `Found you to within ${acc} m. Check the pin is on your building, then lock it.`);
    }, 10000);
  }

  const label = addr ? [addr.title, addr.detail].filter(Boolean).join(", ") : "";

  return (
    <div className="picker">
      <div className="picker-search">
        <div style={{ display: "flex", gap: 8 }}>
          <div style={{ position: "relative", flex: 1 }}>
            <Search size={16} style={{ position: "absolute", left: 12, top: 14, color: "var(--muted)" }} />
            <input className="input" style={{ paddingLeft: 36 }} value={query} onChange={(e) => setQuery(e.target.value)}
              placeholder="Your building, society, road or a landmark near home" aria-label="Search for your building or street" autoComplete="off" />
          </div>
          <button className="btn quiet" onClick={useDevice} disabled={busy} title="Start from your browser's location"><Crosshair size={16} /> Locate me</button>
        </div>
        {results.length > 0 && (
          <div className="results" role="listbox">
            {results.map((r) => (
              <button key={`${r.lat},${r.lon}`} role="option" onClick={() => choose(r)}>
                <MapPin size={14} style={{ verticalAlign: -2, color: "var(--signal)" }} /> <b>{r.title}</b>{r.detail && <span className="muted small"> · {r.detail}</span>}
              </button>
            ))}
          </div>
        )}
      </div>

      <MapView center={view} zoom={initial ? 17 : 4} flyZoom={18} onPick={pick} height={380} />

      <p className="small muted" style={{ margin: 0 }}>
        {note || "Can't find your building by name? Search your road or a landmark, switch to Satellite, then tap your roof."}
      </p>

      <div className="lock-bar">
        <div>
          <div className="kicker">Base camp</div>
          <div className="addr">{pin ? (label || "Looking up this spot…") : "Search or tap the map to drop your pin"}</div>
        </div>
        <div className="actions">
          {onCancel && <button className="btn quiet" onClick={onCancel}>Cancel</button>}
          <button className="btn primary" disabled={!pin} onClick={() => onLock({ ...pin, label: label || "My base camp" })}><Lock size={16} /> Lock base camp</button>
        </div>
      </div>
    </div>
  );
}
