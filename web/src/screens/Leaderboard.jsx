import { useEffect, useState } from "react";
import { api } from "../lib/api.js";

export default function Leaderboard({ player }) {
  const [scope, setScope] = useState(player?.area ? "area" : "week");
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setRows(null);
    setError("");
    api.leaderboard(scope, scope === "area" ? player?.area : undefined).then(setRows).catch((e) => setError(e.message));
  }, [scope, player?.area]);

  return (
    <div className="wrap page" style={{ maxWidth: 860 }}>
      <div className="page-head">
        <div><div className="kicker">Who's been outside the most</div><h1>Leaderboard</h1></div>
        <div className="seg" role="group" aria-label="Range">
          {player?.area && <button aria-pressed={scope === "area"} onClick={() => setScope("area")}>{player.area}</button>}
          <button aria-pressed={scope === "week"} onClick={() => setScope("week")}>This week</button>
          <button aria-pressed={scope === "all"} onClick={() => setScope("all")}>All time</button>
        </div>
      </div>
      <div className="card">
        {error && <p className="error">{error}</p>}
        {!rows && !error && <div className="skeleton" style={{ height: 120 }} />}
        {rows?.length === 0 && <p className="muted">Nobody's finished a quest here yet. That spot at the top is yours.</p>}
        {rows?.length > 0 && (
          <table className="board">
            <thead><tr><th>#</th><th>Explorer</th><th className="num">Quests</th><th className="num">Cards</th><th className="num">XP</th></tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.id} className={r.id === player?.id ? "me" : undefined}>
                  <td className="rank">{i + 1}</td>
                  <td><b>{r.handle}</b> <span className="small muted">lvl {r.level}{r.area ? ` · ${r.area}` : ""}</span></td>
                  <td className="num">{r.quests}</td>
                  <td className="num">{r.cards}</td>
                  <td className="num"><b>{r.xp}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
