export default function PlayerBar({ player }) {
  const span = player.next_level_at - player.level_floor;
  const pct = Math.min(100, ((player.xp - player.level_floor) / span) * 100);
  return (
    <section className="player" aria-label="Your progress">
      <div className="lvl" title={`Level ${player.level}`}>{player.level}</div>
      <div>
        <div className="player-name">{player.handle} <span className="player-title">· {player.title}</span></div>
        <div className="xpbar" role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
          <div style={{ width: `${pct}%` }} />
        </div>
        <div className="xptext">{player.xp} XP · {player.next_level_at - player.xp} XP to level {player.level + 1}</div>
      </div>
      <div className="streak">
        <b>{player.streak > 0 ? "🔥" : "🌱"} {player.streak}</b>
        <span>day streak</span>
      </div>
    </section>
  );
}
