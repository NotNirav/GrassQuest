import { useState } from "react";
import { api } from "../lib/api.js";
import OllamaStatus from "../components/OllamaStatus.jsx";

export default function Setup({ settings, onDone }) {
  const [handle, setHandle] = useState("");
  const [local, setLocal] = useState({ ollamaUrl: settings.ollamaUrl, model: settings.model });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function start(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      onDone(await api.createUser(handle.trim()), local);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="setup">
      <div className="hero">
        <div className="leaf-spin">🌿</div>
        <h1>GrassQuest</h1>
        <p>Tiny real-world quests that get you off the screen. Snap a photo as proof, and an open-source AI on your own computer judges it.</p>
      </div>

      <form className="card" onSubmit={start}>
        <h2>1 · Your local judge</h2>
        <OllamaStatus url={local.ollamaUrl} model={local.model} onChange={(p) => setLocal((s) => ({ ...s, ...p }))} />

        <h2 style={{ marginTop: 18 }}>2 · Pick an adventurer name</h2>
        <div className="field">
          <label htmlFor="handle">Name (shown on the leaderboard)</label>
          <input id="handle" className="input" value={handle} onChange={(e) => setHandle(e.target.value)}
            placeholder="e.g. MossBoss" maxLength={24} autoComplete="off" required minLength={2} />
        </div>
        <button className="btn primary big" disabled={busy || handle.trim().length < 2}>
          {busy ? "Creating…" : "Start my first quest →"}
        </button>
        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
}
