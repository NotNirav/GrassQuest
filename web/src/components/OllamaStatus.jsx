import { useCallback, useEffect, useState } from "react";
import { listModels, RECOMMENDED_MODEL } from "../lib/gemma.js";

/** Checks the player's local Ollama and lets them pick a vision model. */
export default function OllamaStatus({ url, model, onChange }) {
  const [state, setState] = useState({ status: "checking", models: [] });

  const check = useCallback(async () => {
    setState({ status: "checking", models: [] });
    try {
      const models = (await listModels(url)).filter((m) => m.vision || /gemma/i.test(m.name));
      setState({ status: models.length ? "ok" : "nomodel", models });
      if (models.length && !models.some((m) => m.name === model)) {
        const gemma = models.find((m) => /gemma/i.test(m.name)) ?? models[0];
        onChange({ model: gemma.name });
      }
    } catch (e) {
      setState({ status: e.message, models: [] });
    }
  }, [url, model, onChange]);

  useEffect(() => {
    check();
  }, [url]); // eslint-disable-line react-hooks/exhaustive-deps

  const origin = window.location.origin;

  return (
    <div>
      {state.status === "checking" && <div className="status">⏳ Looking for Ollama at {url}…</div>}
      {state.status === "ok" && (
        <>
          <div className="status ok">✅ Ollama found. Your photos will be judged on this computer and never uploaded.</div>
          <div className="field">
            <label htmlFor="model">Judge model</label>
            <select id="model" className="input" value={model} onChange={(e) => onChange({ model: e.target.value })}>
              {state.models.map((m) => (
                <option key={m.name} value={m.name}>{m.name} · {m.sizeGB.toFixed(1)} GB</option>
              ))}
            </select>
          </div>
        </>
      )}
      {state.status === "nomodel" && (
        <div className="status bad">
          <div>
            Ollama is running, but there's no Gemma vision model yet. Run this in a terminal (≈7 GB download, once):
            <div className="code">ollama pull {RECOMMENDED_MODEL}</div>
            <button className="btn ghost" onClick={check}>Check again</button>
          </div>
        </div>
      )}
      {(state.status === "unreachable" || state.status === "blocked") && (
        <div className="status bad">
          <div>
            <b>Can't talk to Ollama.</b> GrassQuest uses Gemma running on your own computer through Ollama.
            <ol className="steps">
              <li>Install Ollama from <a href="https://ollama.com/download" target="_blank" rel="noreferrer">ollama.com/download</a>.</li>
              <li>Pull the model: <div className="code">ollama pull {RECOMMENDED_MODEL}</div></li>
              <li>
                Let this website talk to it. Quit Ollama, then set <code>OLLAMA_ORIGINS</code> and start it again.
                <br />Windows (PowerShell):
                <div className="code">{`setx OLLAMA_ORIGINS "${origin}"`}</div>
                macOS: <div className="code">{`launchctl setenv OLLAMA_ORIGINS "${origin}"`}</div>
                Linux: <div className="code">{`OLLAMA_ORIGINS="${origin}" ollama serve`}</div>
              </li>
            </ol>
            <button className="btn ghost" onClick={check}>Check again</button>
          </div>
        </div>
      )}
    </div>
  );
}
