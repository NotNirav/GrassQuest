import { useEffect, useState } from "react";
import { api } from "../lib/api.js";
import Faq from "../components/Faq.jsx";

export default function Profile({ player, model, settings, onChangePlace, onLogout }) {
  const [all, setAll] = useState([]);
  useEffect(() => { api.badges().then(setAll).catch(() => {}); }, []);
  const have = new Set(player.badges.map((b) => b.key));
  const pct = Math.min(100, ((player.xp - player.level_floor) / (player.next_level_at - player.level_floor)) * 100);

  return (
    <div className="wrap page">
      <div className="page-head">
        <div><div className="kicker">Level {player.level} · {player.title}</div><h1>{player.handle}</h1></div>
      </div>
      <div className="card" style={{ marginBottom: 18 }}>
        <div className="kicker">{player.xp} XP · {player.next_level_at - player.xp} to level {player.level + 1}</div>
        <div className="odds" style={{ height: 10 }}><div style={{ width: `${pct}%`, background: "var(--signal)" }} /></div>
      </div>
      <div className="stats" style={{ marginBottom: 28 }}>
        <div className="stat"><b>{player.completed}</b><span className="muted small">quests done</span></div>
        <div className="stat"><b>{player.streak}</b><span className="muted small">day streak (best {player.best_streak})</span></div>
        <div className="stat"><b>{player.field_guide.length}</b><span className="muted small">Field Guide cards</span></div>
        <div className="stat"><b>{player.seeds}</b><span className="muted small">Seeds</span></div>
      </div>

      <h2 style={{ fontSize: "1.8rem", textTransform: "uppercase", marginBottom: 12 }}>Badges · {have.size}/{all.length || "…"}</h2>
      <div className="badges" style={{ marginBottom: 32 }}>
        {all.map((b) => <div key={b.key} className={`badge${have.has(b.key) ? "" : " locked"}`}><div className="ic">{b.icon}</div><b>{b.name}</b><span>{b.description}</span></div>)}
      </div>

      <div className="split" style={{ alignItems: "start" }}>
        <div className="card">
          <h2 style={{ fontSize: "1.5rem", marginBottom: 10 }}>Settings</h2>
          <p className="small"><b>Location:</b> {settings.place?.label} <button className="btn link" onClick={onChangePlace}>change</button></p>
          <p className="small"><b>Judge model:</b> {model || "not found (is Ollama running?)"}</p>
          <p className="small muted">No passwords: your explorer lives in this browser.</p>
          <button className="btn quiet" onClick={() => confirm("Sign out? You can't get this explorer back on this browser.") && onLogout()}>Sign out</button>
        </div>
        <div>
          <h2 style={{ fontSize: "1.5rem", marginBottom: 6 }}>FAQ</h2>
          <Faq />
        </div>
      </div>
    </div>
  );
}
