import { DEFAULT_OLLAMA, RECOMMENDED_MODEL } from "./gemma.js";

const KEY = "sidequests.settings";
const DEFAULTS = { userId: null, ollamaUrl: DEFAULT_OLLAMA, model: RECOMMENDED_MODEL, voice: true };

export function loadSettings() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || "{}") };
  } catch {
    return { ...DEFAULTS };
  }
}

export function saveSettings(s) {
  try {
    localStorage.setItem(KEY, JSON.stringify(s));
  } catch {
    /* private mode: settings just won't persist */
  }
}
