/** GrassQuest mark: a map pin whose inside is three blades of grass, sitting on a topo contour. */
export function LogoMark({ size = 30 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="GrassQuest">
      <rect width="64" height="64" rx="16" fill="var(--signal)" />
      <path d="M8 50 C 20 44, 30 54, 42 48 S 58 46, 58 46" fill="none" stroke="#fff" strokeOpacity=".35" strokeWidth="2" />
      <path d="M32 9 C 21.5 9 14 16.8 14 26.6 C 14 39 32 55 32 55 C 32 55 50 39 50 26.6 C 50 16.8 42.5 9 32 9Z" fill="#fff" />
      <path d="M32 40 C 31 32 29 26 24 20 M32 40 C 32.6 31 33 24 32 16 M32 40 C 34 33 37 28 41 23"
        fill="none" stroke="var(--signal)" strokeWidth="3.4" strokeLinecap="round" />
    </svg>
  );
}

export default function Logo({ light = false }) {
  return (
    <span className="logo" style={light ? { color: "#fff" } : undefined}>
      <LogoMark />
      GrassQuest
    </span>
  );
}
