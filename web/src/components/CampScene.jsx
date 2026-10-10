/** The player's Basecamp. Every slot's tier changes what's drawn. Sky follows the real time of day. */
export default function CampScene({ camp, phase = "day" }) {
  const t = Object.fromEntries(camp.map((c) => [c.slot, c.tier]));
  const sky = { night: ["#0e1a2b", "#24344d"], golden: ["#f6a04d", "#fbd38a"], morning: ["#9cc7e8", "#f4e3c1"], day: ["#8fc1e3", "#dcecf5"] }[phase] ?? ["#8fc1e3", "#dcecf5"];
  const night = phase === "night";
  return (
    <svg className="camp-scene" viewBox="0 0 800 380" role="img" aria-label="Your Basecamp">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={sky[0]} /><stop offset="1" stopColor={sky[1]} /></linearGradient>
        <radialGradient id="glow"><stop offset="0" stopColor="#ffb347" stopOpacity=".75" /><stop offset="1" stopColor="#ffb347" stopOpacity="0" /></radialGradient>
      </defs>
      <rect width="800" height="380" fill="url(#sky)" />
      {night ? <circle cx="660" cy="70" r="26" fill="#f4efe0" /> : <circle cx="660" cy="80" r="34" fill={phase === "golden" ? "#ff7a2f" : "#ffd45a"} />}
      {night && [[90, 50], [180, 90], [300, 40], [420, 80], [520, 30], [740, 140], [600, 120]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="1.8" fill="#fff" />)}
      <path d="M0 250 L120 150 L230 230 L360 120 L500 240 L620 160 L800 250 L800 380 L0 380Z" fill={night ? "#1d2a3a" : "#7b8f9e"} opacity=".55" />
      <path d="M0 280 L150 210 L300 270 L450 200 L620 270 L800 220 L800 380 L0 380Z" fill={night ? "#18241b" : "#5d7a4c"} />
      <rect y="300" width="800" height="80" fill={night ? "#141c14" : "#6f8f55"} />
      {[40, 90, 700, 760].map((x, i) => (
        <g key={i} transform={`translate(${x} ${270 + (i % 2) * 10})`}>
          <rect x="-4" y="20" width="8" height="26" fill="#4a3426" />
          <path d="M0 -30 L26 26 L-26 26Z" fill={night ? "#1f3324" : "#2f5a33"} />
        </g>
      ))}

      {/* flag */}
      {t.flag > 0 && (
        <g transform="translate(560 200)">
          <rect x="0" y="0" width="5" height="110" fill="#3b2a1f" />
          {t.flag === 1 && <path d="M5 4 L55 18 L5 32Z" fill="#ff5b1f" />}
          {t.flag === 2 && <rect x="5" y="4" width="60" height="38" fill="#ff5b1f" />}
          {t.flag === 3 && <><rect x="5" y="4" width="70" height="44" fill="#ff5b1f" /><path d="M20 38 L40 14 L60 38Z" fill="#fff" /></>}
        </g>
      )}
      {t.flag === 0 && <rect x="560" y="200" width="5" height="110" fill="#3b2a1f" opacity=".6" />}

      {/* shelter */}
      <g transform="translate(220 300)">
        {t.shelter === 0 && <rect x="-50" y="-10" width="100" height="14" rx="7" fill="#8a5a3b" />}
        {t.shelter === 1 && <><path d="M-80 0 L0 -100 L80 0Z" fill="#ff5b1f" /><path d="M-14 0 L0 -40 L14 0Z" fill="#7a2c0d" /></>}
        {t.shelter === 2 && <>
          <rect x="-80" y="-80" width="160" height="80" fill="#8a5a3b" /><path d="M-95 -78 L0 -140 L95 -78Z" fill="#5a3a26" />
          <rect x="-18" y="-46" width="36" height="46" fill="#3b2a1f" /><rect x="34" y="-60" width="30" height="24" fill={night ? "#ffd27a" : "#cfe6f5"} />
        </>}
        {t.shelter === 3 && <>
          <rect x="-12" y="-150" width="24" height="150" fill="#5a3a26" /><circle cx="0" cy="-200" r="80" fill={night ? "#1f3324" : "#2f5a33"} />
          <rect x="-60" y="-190" width="120" height="60" fill="#8a5a3b" /><path d="M-72 -188 L0 -232 L72 -188Z" fill="#ff5b1f" />
          <rect x="22" y="-176" width="24" height="20" fill={night ? "#ffd27a" : "#cfe6f5"} />
          <path d="M40 -130 L40 0 M28 -110 L52 -110 M28 -80 L52 -80 M28 -50 L52 -50 M28 -20 L52 -20" stroke="#3b2a1f" strokeWidth="4" />
        </>}
      </g>

      {/* fire */}
      <g transform="translate(400 318)">
        {t.fire > 0 && <circle r={40 + t.fire * 18} fill="url(#glow)" />}
        <path d="M-26 6 L26 -6 M-26 -6 L26 6" stroke="#5a3a26" strokeWidth="7" strokeLinecap="round" />
        {t.fire >= 2 && [-34, -17, 0, 17, 34].map((x) => <circle key={x} cx={x} cy="10" r="8" fill="#8c8c8c" />)}
        {t.fire >= 1 && <path d={`M0 -${18 + t.fire * 14} C 18 -10 14 4 0 4 C -14 4 -18 -10 0 -${18 + t.fire * 14}Z`} fill="#ff7a1f" />}
        {t.fire >= 1 && <path d={`M0 -${8 + t.fire * 8} C 9 -6 7 2 0 2 C -7 2 -9 -6 0 -${8 + t.fire * 8}Z`} fill="#ffd45a" />}
      </g>

      {/* light */}
      {t.light === 1 && <g transform="translate(330 270)"><rect x="-2" y="0" width="4" height="40" fill="#3b2a1f" /><rect x="-10" y="-16" width="20" height="18" rx="3" fill="#ffd27a" /></g>}
      {t.light >= 2 && <path d="M120 200 Q 300 240 480 196" fill="none" stroke="#3b2a1f" strokeWidth="2" />}
      {t.light >= 2 && [150, 190, 230, 270, 310, 350, 390, 430].map((x, i) => <circle key={x} cx={x} cy={205 + Math.sin(i / 1.3) * 10 + (i > 1 && i < 6 ? 14 : 4)} r="5" fill={["#ff5b1f", "#ffd27a", "#7fd1ff"][i % 3]} />)}
      {t.light === 3 && <g transform="translate(470 250)"><rect x="-10" y="-60" width="20" height="60" fill="#e8e0cf" /><rect x="-14" y="-74" width="28" height="16" fill="#ffd27a" /><path d="M14 -66 L120 -96 L120 -36Z" fill="#ffd27a" opacity=".35" /></g>}

      {/* gear */}
      {t.gear >= 1 && <g transform="translate(300 318)"><rect x="-16" y="-34" width="32" height="34" rx="6" fill="#2f5d8a" /><rect x="-10" y="-26" width="20" height="10" rx="3" fill="#24496d" /></g>}
      {t.gear >= 2 && <g transform="translate(340 330)"><circle cx="-8" cy="0" r="7" fill="#17140f" /><circle cx="8" cy="0" r="7" fill="#17140f" /></g>}
      {t.gear === 3 && <g transform="translate(640 300)"><path d="M0 0 L-16 40 M0 0 L16 40 M0 0 L0 40" stroke="#3b2a1f" strokeWidth="3" /><rect x="-36" y="-14" width="56" height="14" rx="4" transform="rotate(-24)" fill="#c98a00" /></g>}

      {/* companion */}
      {t.companion === 1 && <g transform="translate(470 336)"><ellipse rx="14" ry="6" fill="#8a6a4a" /><circle cx="6" cy="-8" r="8" fill="#c9a26b" stroke="#8a6a4a" strokeWidth="2" /></g>}
      {t.companion === 2 && <g transform="translate(480 326)"><ellipse rx="22" ry="11" fill="#e0662b" /><circle cx="22" cy="-8" r="10" fill="#e0662b" /><path d="M16 -16 L20 -28 L26 -16Z M24 -16 L30 -27 L32 -14Z" fill="#e0662b" /><path d="M-22 0 Q -44 -16 -36 6" stroke="#e0662b" strokeWidth="9" fill="none" strokeLinecap="round" /></g>}
      {t.companion === 3 && <g transform="translate(608 196)"><ellipse rx="16" ry="20" fill="#8a6a4a" /><circle cx="-6" cy="-6" r="5" fill="#fff" /><circle cx="6" cy="-6" r="5" fill="#fff" /><circle cx="-6" cy="-6" r="2" fill="#17140f" /><circle cx="6" cy="-6" r="2" fill="#17140f" /></g>}
    </svg>
  );
}
