import { useEffect, useState } from "react";
import { api } from "../lib/api.js";

export default function Leaderboard({ me }) {
  const [scope, setScope] = useState("week");
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setRows(null);
    setError("");
    api.leaderboard(scope).then(setRows).catch((e) => setError(e.message));
  }, [scope]);

  return (
    <section className="card">
      <h2>Leaderboard</h2>
      <div className="tabs" role="group" aria-label="Time range">
        <button aria-pressed={scope === "week"} onClick={() => setScope("week")}>This week</button>
        <button aria-pressed={scope === "all"} onClick={() => setScope("all")}>All time</button>
      </div>
      {error && <p className="error">{error}</p>}
      {!rows && !error && <p className="muted">Loading…</p>}
      {rows && rows.length === 0 && <p className="muted">Nobody has finished a quest {scope === "week" ? "this week" : "yet"}. Be the first.</p>}
      {rows && rows.length > 0 && (
        <table className="board">
          <thead>
            <tr><th>#</th><th>Adventurer</th><th className="num">Quests</th><th className="num">XP</th></tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.id} className={r.id === me ? "me" : undefined}>
                <td className="rank">{["🥇", "🥈", "🥉"][i] ?? i + 1}</td>
                <td>{r.handle} <span className="muted small">· lvl {r.level}</span></td>
                <td className="num">{r.quests}</td>
                <td className="num"><b>{r.xp}</b></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
