// The Ranger's voice: 16 lines generated once with ElevenLabs (scripts/make_voice.py), served as static files.
// Playing them costs nothing; no ElevenLabs call happens during play.
const KEY = "grassquest.voice";
let queue = [];
let current = null;

export const voiceOn = () => { try { return localStorage.getItem(KEY) !== "off"; } catch { return true; } };
export const setVoice = (on) => { try { localStorage.setItem(KEY, on ? "on" : "off"); } catch { /* ignore */ } if (!on) stopRanger(); };

export function ranger(...ids) {
  if (!voiceOn()) return;
  queue.push(...ids.filter(Boolean));
  if (!current) next();
}

function next() {
  const id = queue.shift();
  if (!id) { current = null; return; }
  current = new Audio(`/voice/${id}.mp3`);
  current.onended = next;
  current.onerror = next;
  current.play().catch(next); // autoplay blocked or file missing: skip quietly
}

export function stopRanger() {
  queue = [];
  if (current) { current.pause(); current = null; }
}

/** Which "head out" line fits the real conditions. */
export function departureLine(ctx) {
  const band = ctx?.weather?.band;
  const phase = ctx?.sun?.phase;
  if (band === "severe") return "rain-check";
  if (band === "rain" || band === "drizzle") return "go-rain";
  if (band === "hot") return "go-hot";
  if (phase === "night") return "go-night";
  if (phase === "golden") return "go-golden";
  if (phase === "morning") return "go-morning";
  if (["cloudy", "fog", "windy", "cold"].includes(band)) return "go-cloudy";
  return "go-clear";
}
