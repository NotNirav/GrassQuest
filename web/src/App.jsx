import { useCallback, useEffect, useState } from "react";
import { BookOpen, Coins, Flame, Map, Tent, Trophy, User, Volume2, VolumeX } from "lucide-react";
import { ranger, setVoice, voiceOn } from "./lib/ranger.js";
import Logo from "./components/Logo.jsx";
import { api } from "./lib/api.js";
import { detectGemma, warmUp } from "./lib/gemma.js";
import { loadSettings, saveSettings } from "./lib/settings.js";
import Landing from "./screens/Landing.jsx";
import Setup from "./screens/Setup.jsx";
import Today from "./screens/Today.jsx";
import Basecamp from "./screens/Basecamp.jsx";
import FieldGuide from "./screens/FieldGuide.jsx";
import Leaderboard from "./screens/Leaderboard.jsx";
import Profile from "./screens/Profile.jsx";

const TABS = [
  ["today", "Today", Map],
  ["camp", "Basecamp", Tent],
  ["guide", "Field Guide", BookOpen],
  ["board", "Leaderboard", Trophy],
  ["me", "Profile", User],
];

export default function App() {
  const [settings, setSettings] = useState(loadSettings);
  const [player, setPlayer] = useState(null);
  const [model, setModel] = useState(null);
  const [tab, setTab] = useState("today");
  const [focus, setFocus] = useState(false);
  const [started, setStarted] = useState(false);
  const [voice, setVoiceState] = useState(voiceOn);

  const update = useCallback((patch) => {
    setSettings((s) => {
      const next = { ...s, ...patch };
      saveSettings(next);
      return next;
    });
  }, []);

  useEffect(() => {
    if (!settings.userId) return;
    api.user(settings.userId).then(setPlayer).catch((e) => e.status === 404 && update({ userId: null }));
  }, [settings.userId, update]);

  useEffect(() => {
    detectGemma(settings.ollamaUrl).then((r) => {
      setModel(r.status === "ok" ? r.model : null);
      if (r.status === "ok") warmUp(settings.ollamaUrl, r.model);
    });
  }, [settings.ollamaUrl]);

  useEffect(() => { window.scrollTo(0, 0); }, [tab]);

  if (!settings.userId || !settings.place) {
    if (!settings.userId && !started) return <Landing onStart={() => setStarted(true)} />;
    return (
      <>
        <Nav />
        <Setup settings={settings} existing={!!settings.userId}
          onDone={(user, patch) => { update({ ...patch, ...(user ? { userId: user.id } : {}) }); if (user) { setPlayer(user); ranger("welcome"); } }} />
      </>
    );
  }

  const hour = new Date().getHours();
  const phase = hour < 6 || hour >= 19 ? "night" : hour < 9 ? "morning" : hour >= 17 ? "golden" : "day";

  return (
    <>
      {!focus && (
        <Nav>
          <nav className="tabs" aria-label="Main">
            {TABS.map(([key, label, Icon]) => (
              <button key={key} aria-current={tab === key ? "page" : undefined} onClick={() => setTab(key)}><Icon size={17} />{label}</button>
            ))}
          </nav>
          {player && (
            <div className="wallet">
              <span title="Streak"><Flame size={17} color="var(--signal)" />{player.streak}</span>
              <span title="Seeds"><Coins size={17} />{player.seeds}</span>
              <span className="lvl-label" title="Level">Lv {player.level}</span>
              <button className="btn link" style={{ padding: 0 }} title={voice ? "Mute the Ranger" : "Unmute the Ranger"} aria-label={voice ? "Mute the Ranger" : "Unmute the Ranger"}
                onClick={() => { setVoice(!voice); setVoiceState(!voice); }}>{voice ? <Volume2 size={18} /> : <VolumeX size={18} />}</button>
            </div>
          )}
        </Nav>
      )}
      <main>
        <div hidden={tab !== "today"}>
          <Today settings={settings} model={model} player={player} onPlayer={setPlayer} onFocus={setFocus} onPlace={(place) => update({ place })} />
        </div>
        {tab === "camp" && player && <Basecamp player={player} phase={phase} onPlayer={setPlayer} />}
        {tab === "guide" && player && <FieldGuide player={player} />}
        {tab === "board" && <Leaderboard player={player} />}
        {tab === "me" && player && (
          <Profile player={player} model={model} settings={settings}
            onChangePlace={() => update({ place: null })}
            onLogout={() => { update({ userId: null, place: null }); setPlayer(null); setStarted(false); }} />
        )}
      </main>
    </>
  );
}

function Nav({ children }) {
  return (
    <header className="nav">
      <div className="wrap nav-in">
        <Logo />
        {children}
      </div>
    </header>
  );
}
