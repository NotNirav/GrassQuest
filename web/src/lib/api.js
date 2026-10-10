const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function localDate() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
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

const post = (path, body) => call(path, { method: "POST", body });

export const api = {
  createUser: (handle) => post("/api/users", { handle }),
  user: (id) => call(`/api/users/${id}?today=${localDate()}`),
  context: (lat, lon) => post("/api/context", { lat, lon }),
  geocode: (q) => call(`/api/geocode?q=${encodeURIComponent(q)}`),
  today: (userId, place, exclude = []) => post("/api/quests/today", { user_id: userId, lat: place.lat, lon: place.lon, exclude }),
  accept: (offerId) => post(`/api/offers/${offerId}/accept`, {}),
  verdict: (offerId, v) => post(`/api/offers/${offerId}/verdict`, v),
  giveUp: (offerId) => post(`/api/offers/${offerId}/giveup`, {}),
  buyCamp: (userId, slot) => post("/api/camp/buy", { user_id: userId, slot, today: localDate() }),
  buyFreeze: (userId) => post("/api/freeze/buy", { user_id: userId, today: localDate() }),
  leaderboard: (scope, area) => call(`/api/leaderboard?scope=${scope}&today=${localDate()}${area ? `&area=${encodeURIComponent(area)}` : ""}`),
  badges: () => call("/api/badges"),
};
