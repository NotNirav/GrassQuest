import { useCallback, useEffect, useState } from "react";
import { Check, Cpu, MapPin, RefreshCw, User, X } from "lucide-react";
import { api } from "../lib/api.js";
import BasePicker from "../components/BasePicker.jsx";
import { detectGemma, MIN_MODEL } from "../lib/gemma.js";

export default function Setup({ settings, existing = false, onDone }) {
  const [place, setPlace] = useState(settings.place);  // null while (re)setting base camp
  const [ai, setAi] = useState({ status: "checking" });
  const [handle, setHandle] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const checkAi = useCallback(async () => {
    setAi({ status: "checking" });
    setAi(await detectGemma(settings.ollamaUrl));
  }, [settings.ollamaUrl]);
  useEffect(() => { checkAi(); }, [checkAi]);

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
    <div className="wrap setup" style={{ maxWidth: 820 }}>
      <div className="kicker">Before you head out</div>
      <h1 style={{ fontSize: "clamp(2.4rem,6vw,4rem)", textTransform: "uppercase", margin: "6px 0 24px" }}>Three quick checks</h1>

      <section className={`check ${place ? "ok" : ""}`}>
        <div className="check-dot">{place ? <Check /> : <MapPin />}</div>
        <div style={{ minWidth: 0 }}>
          <h3>Your base camp</h3>
          {place ? (
            <p className="muted" style={{ margin: 0 }}>{place.label} <button className="btn link" onClick={() => setPlace(null)}>move</button></p>
          ) : (
            <>
              <p className="muted" style={{ margin: "0 0 12px" }}>Where your quests start from: your home, building or hostel. Set it once. It stays in this browser; the server only uses it to measure distances.</p>
              <BasePicker initial={settings.place ?? settings.lastPlace} onLock={(p) => { setPlace(p); api.context(p.lat, p.lon).catch(() => {}); }} />
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
