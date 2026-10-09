import { useCallback, useEffect, useState } from "react";
import { api } from "./lib/api.js";
import { loadSettings, saveSettings } from "./lib/settings.js";
import Setup from "./screens/Setup.jsx";
import QuestFlow from "./screens/QuestFlow.jsx";
import Leaderboard from "./screens/Leaderboard.jsx";
import Profile from "./screens/Profile.jsx";
import PlayerBar from "./components/PlayerBar.jsx";

const TABS = [
  ["quest", "Quest"],
  ["board", "Leaderboard"],
  ["me", "Profile"],
];

export default function App() {
  const [settings, setSettings] = useState(loadSettings);
  const [player, setPlayer] = useState(null);
  const [tab, setTab] = useState("quest");
  const [focus, setFocus] = useState(false); // hides chrome while the player is outside

  const update = useCallback((patch) => {
    setSettings((s) => {
      const next = { ...s, ...patch };
      saveSettings(next);
      return next;
    });
  }, []);

  const refreshPlayer = useCallback(async () => {
    if (!settings.userId) return;
    try {
      setPlayer(await api.user(settings.userId));
    } catch (e) {
      if (e.status === 404) update({ userId: null }); // server was reset: start over
    }
  }, [settings.userId, update]);

  useEffect(() => {
    refreshPlayer();
  }, [refreshPlayer]);

  if (!settings.userId) {
    return (
      <div className="shell">
        <Setup settings={settings} onDone={(user, patch) => { update({ ...patch, userId: user.id }); setPlayer(user); }} />
      </div>
    );
  }

  return (
    <div className="shell">
      {!focus && (
        <header className="topbar">
          <div className="brand"><span className="brand-mark">🌿</span>Side Quests</div>
          <nav className="nav" aria-label="Main">
            {TABS.map(([key, label]) => (
              <button key={key} aria-current={tab === key ? "page" : undefined} onClick={() => setTab(key)}>{label}</button>
            ))}
          </nav>
        </header>
      )}
      {!focus && player && <PlayerBar player={player} />}
      {/* stays mounted so switching tabs doesn't throw away the current quest */}
      <div hidden={tab !== "quest"}>
        <QuestFlow settings={settings} player={player} onPlayer={setPlayer} onFocus={setFocus} />
      </div>
      {tab === "board" && <Leaderboard me={settings.userId} />}
      {tab === "me" && player && (
        <Profile player={player} settings={settings} onSettings={update} onLogout={() => { update({ userId: null }); setPlayer(null); }} />
      )}
    </div>
  );
}
