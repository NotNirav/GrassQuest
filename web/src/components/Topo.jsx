import { useMemo } from "react";

/** Topographic contour lines, drawn procedurally so every page gets its own "terrain". */
export default function Topo({ seed = 1, rings = 14 }) {
  const paths = useMemo(() => {
    const rnd = mulberry(seed);
    const hills = Array.from({ length: 3 }, () => ({ x: 120 + rnd() * 760, y: 80 + rnd() * 440, k: 0.6 + rnd() * 0.8, ph: rnd() * 6 }));
    const out = [];
    for (const h of hills) {
      for (let i = 1; i <= rings; i++) {
        const r = i * 26 * h.k;
        const pts = [];
        for (let a = 0; a <= 64; a++) {
          const t = (a / 64) * Math.PI * 2;
          const wob = 1 + 0.16 * Math.sin(3 * t + h.ph + i * 0.3) + 0.08 * Math.sin(7 * t - h.ph);
          pts.push(`${(h.x + Math.cos(t) * r * wob * 1.35).toFixed(1)},${(h.y + Math.sin(t) * r * wob).toFixed(1)}`);
        }
        out.push(`M${pts.join("L")}Z`);
      }
    }
    return out;
  }, [seed, rings]);
  return (
    <svg className="topo" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {paths.map((d, i) => <path key={i} d={d} fill="none" stroke="currentColor" strokeWidth={i % 5 === 4 ? 1.6 : 0.8} />)}
    </svg>
  );
}

function mulberry(a) {
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
