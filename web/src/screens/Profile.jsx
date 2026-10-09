import { useEffect, useState } from "react";
import { api } from "../lib/api.js";
import OllamaStatus from "../components/OllamaStatus.jsx";

const CATEGORY_ICON = { plants: "🌿", birds: "🐦", sky: "☁️", walking: "🥾", water: "💧", textures: "🪨", social: "🧺" };

export default function Profile({ player, settings, onSettings, onLogout }) {
  const [allBadges, setAllBadges] = useState([]);
  useEffect(() => {
    api.badges().then(setAllBadges).catch(() => {});
  }, []);
  const earned = new Set(player.badges.map((b) => b.key));

  return (
    <div className="grid">
      <div className="stack">
        <section className="card">
          <h2>Badges · {earned.size}/{allBadges.length || "…"}</h2>
          <div className="badges">
            {allBadges.map((b) => (
              <div key={b.key} className={`badge${earned.has(b.key) ? "" : " locked"}`}>
                <div className="icon">{b.icon}</div>
                <div className="name">{b.name}</div>
                <div className="desc">{b.description}</div>
              </div>
            ))}
          </div>
        </section>
        <section className="card">
          <h2>Your quest log</h2>
          <p className="muted small" style={{ marginTop: -6 }}>
            {player.completed} quests completed · best streak {player.best_streak} days
          </p>
          <div className="badges">
            {Object.entries(CATEGORY_ICON).map(([cat, icon]) => (
              <div key={cat} className="badge">
                <div className="icon">{icon}</div>
                <div className="name">{player.counts[cat] ?? 0}</div>
                <div className="desc">{cat}</div>
              </div>
            ))}
          </div>
        </section>
      </div>
      <aside className="stack">
        <section className="card">
          <h2>Settings</h2>
          <div className="field">
            <label htmlFor="ollama">Ollama address</label>
            <input id="ollama" className="input" defaultValue={settings.ollamaUrl}
              onBlur={(e) => onSettings({ ollamaUrl: e.target.value.trim().replace(/\/$/, "") })} />
          </div>
          <OllamaStatus url={settings.ollamaUrl} model={settings.model} onChange={onSettings} />
          <label className="toggle">
            <input type="checkbox" checked={settings.voice} onChange={(e) => onSettings({ voice: e.target.checked })} />
            Narrator voice
          </label>
        </section>
        <section className="card">
          <h2>Account</h2>
          <p className="muted small">There are no passwords. Your player is saved in this browser only.</p>
          <button className="btn danger" onClick={() => confirm("Sign out? You won't be able to get this player back on this browser.") && onLogout()}>
            Sign out
          </button>
        </section>
      </aside>
    </div>
  );
}
