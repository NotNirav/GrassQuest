const ORIGIN = typeof window !== "undefined" ? window.location.origin : "";

const ITEMS = [
  ["What do I need?", <>A computer with <a href="https://ollama.com/download" target="_blank" rel="noreferrer">Ollama</a> and any Gemma 4 model. <code>gemma4:e2b</code> is the smallest (about 7 GB); bigger ones like <code>gemma4:12b</code> judge better if your machine can run them. Your phone is just the camera.</>],
  ["How do I install the model?", <>Install Ollama, then run <code>ollama pull gemma4:e2b</code> in a terminal. GrassQuest finds it automatically.</>],
  ["It says Ollama is blocked. What now?", <>Ollama only answers websites you allow. Quit Ollama, run <code>{`setx OLLAMA_ORIGINS "${ORIGIN}"`}</code> (Windows) or <code>{`launchctl setenv OLLAMA_ORIGINS "${ORIGIN}"`}</code> (macOS), then start Ollama again. On <code>localhost</code> this usually isn't needed.</>],
  ["Do my photos get uploaded?", "No. Gemma judges them on your computer. The server only receives the verdict (pass, close, or not yet) and the name of anything Gemma identified."],
  ["What happens with my location?", "Your exact spot is used only to measure how far nearby parks and ponds are, and is never stored. Weather and map lookups use an area of about 1 km. If the browser guesses wrong, tap the map in setup to move your pin."],
  ["How strict is the judge?", "Not very. There's no prize money, so any honest outdoor photo that fits the quest passes. Close-but-not-quite pays half."],
  ["What if the weather is terrible?", "GrassQuest won't send you into a storm. You'll get a short rain-check quest from your window or doorway, plus a free streak freeze."],
  ["What are Seeds for?", "Seeds build your Basecamp (tent to treehouse, campfire to bonfire, a fox, an owl…) and buy streak freezes for days you can't get out."],
  ["Who picks my quests?", "Code filters what's possible right now (places, weather, daylight). TabPFN, a tabular foundation model, predicts your odds and minutes for each. You get an easy win, a sweet spot and a stretch."],
];

export default function Faq() {
  return ITEMS.map(([q, a]) => (
    <details className="faq" key={q}>
      <summary>{q}</summary>
      <p>{a}</p>
    </details>
  ));
}
