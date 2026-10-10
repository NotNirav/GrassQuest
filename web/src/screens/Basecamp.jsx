import { useState } from "react";
import { Coins, Snowflake } from "lucide-react";
import { api } from "../lib/api.js";
import CampScene from "../components/CampScene.jsx";

export default function Basecamp({ player, phase, onPlayer }) {
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");

  async function buy(slot) {
    setBusy(slot);
    setMsg("");
    try {
      onPlayer(slot === "freeze" ? await api.buyFreeze(player.id) : await api.buyCamp(player.id, slot));
    } catch (e) {
      setMsg(e.message);
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="wrap page">
      <div className="page-head">
        <div><div className="kicker">Spend your Seeds</div><h1>Basecamp</h1></div>
        <span className="pill"><Coins size={16} /> {player.seeds} Seeds</span>
      </div>
      <CampScene camp={player.camp} phase={phase} />
      {msg && <p className="error">{msg}</p>}
      <div className="shop">
        {player.camp.map((c) => (
          <div className="shop-item" key={c.slot}>
            <div className="kicker">{c.name}</div>
            <b style={{ fontSize: "1.15rem" }}>{c.item}</b>
            <div className="tiers">{Array.from({ length: c.max_tier }, (_, i) => <i key={i} className={i < c.tier ? "on" : ""} />)}</div>
            {c.next ? (
              <button className="btn quiet" disabled={busy === c.slot || player.seeds < c.next.price} onClick={() => buy(c.slot)}>
                Upgrade to {c.next.item} · <Coins size={14} /> {c.next.price}
              </button>
            ) : <span className="small muted">Fully upgraded</span>}
          </div>
        ))}
        <div className="shop-item">
          <div className="kicker">Streak freeze</div>
          <b style={{ fontSize: "1.15rem" }}><Snowflake size={16} style={{ verticalAlign: -2 }} /> {player.freezes} / {player.max_freezes} held</b>
          <span className="small muted">Covers a day you can't get outside. Used automatically.</span>
          <button className="btn quiet" disabled={busy === "freeze" || player.seeds < player.freeze_price || player.freezes >= player.max_freezes} onClick={() => buy("freeze")}>
            Buy a freeze · <Coins size={14} /> {player.freeze_price}
          </button>
        </div>
      </div>
    </div>
  );
}
