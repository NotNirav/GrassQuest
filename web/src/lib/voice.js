import { api } from "./api.js";

let current;

// ElevenLabs via our server when available, otherwise the browser's built-in voice.
export async function speak(text) {
  stop();
  const url = await api.tts(text);
  if (url) {
    current = new Audio(url);
    await current.play().catch(() => {});
    return;
  }
  if ("speechSynthesis" in window) {
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.95;
    window.speechSynthesis.speak(u);
  }
}

export function stop() {
  current?.pause();
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
}
