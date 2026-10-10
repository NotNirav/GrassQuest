import { loadSettings } from "./settings.js";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function clock() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return {
    today: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    hour: d.getHours(),
    dow: (d.getDay() + 6) % 7, // Monday = 0
  };
}

async function call(path, { method = "GET", body } = {}) {
  let res;
  try {
    res = await fetch(`${API}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Can't reach the GrassQuest server. Is it running?");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detail = typeof data.detail === "string" ? data.detail : `Server error (${res.status})`;
    throw Object.assign(new Error(detail), { status: res.status });
  }
  return res.json();
}

export const api = {
  createUser: (handle) => call("/api/users", { method: "POST", body: { handle } }),
  user: (id) => call(`/api/users/${id}?today=${clock().today}`),
  nextQuest: (userId, { exclude = [], boss = false } = {}) =>
    call("/api/quests/next", { method: "POST", body: { user_id: userId, exclude, boss, ...clock() } }),
  verdict: (offerId, v) => call(`/api/offers/${offerId}/verdict`, { method: "POST", body: { ...v, ...clock() } }),
  giveUp: (offerId) => call(`/api/offers/${offerId}/giveup`, { method: "POST" }),
  leaderboard: (scope) => call(`/api/leaderboard?scope=${scope}&today=${clock().today}`),
  badges: () => call("/api/badges"),
  health: () => call("/api/health"),
  async tts(text) {
    const res = await fetch(`${API}/api/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, user_id: loadSettings().userId }),
    }).catch(() => null);
    if (!res || res.status !== 200) return null;
    return URL.createObjectURL(await res.blob());
  },
};
