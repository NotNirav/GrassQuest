// Talks to Ollama running on the player's own computer. Photos never leave the machine.

export const DEFAULT_OLLAMA = "http://localhost:11434";
export const RECOMMENDED_MODEL = "gemma4:e2b";

const VERDICT_SCHEMA = {
  type: "object",
  properties: {
    pass: { type: "boolean" },
    confidence: { type: "number" },
    seen: { type: "string" },
    reaction: { type: "string" },
  },
  required: ["pass", "confidence", "seen", "reaction"],
};

export async function listModels(baseUrl) {
  let res;
  try {
    res = await fetch(`${baseUrl}/api/tags`);
  } catch {
    throw new Error("unreachable");
  }
  if (!res.ok) throw new Error(res.status === 403 ? "blocked" : "unreachable");
  const { models = [] } = await res.json();
  return models.map((m) => ({
    name: m.name,
    sizeGB: m.size / 2 ** 30,
    family: m.details?.family ?? "",
    vision: (m.capabilities ?? []).includes("vision"),
  }));
}

async function chat(baseUrl, body) {
  const send = (b) =>
    fetch(`${baseUrl}/api/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) });
  let res = await send({ think: false, ...body });
  if (res.status === 400) res = await send(body); // models without a thinking mode reject `think`
  if (!res.ok) throw new Error(`Ollama error ${res.status}: ${await res.text()}`);
  return res.json();
}

export function judgePrompt(quest) {
  return `You are the friendly but honest judge of "GrassQuest", a game that gets people to go outside.

Quest: "${quest.title}"
What counts as proof: ${quest.proof}

Look at the photo and decide if it shows the player completed this quest.
- Pass real outdoor photos that reasonably match the quest. Be generous with framing and quality.
- Fail photos of screens, stock-looking images, indoor shots for outdoor quests, or anything unrelated.

Reply as JSON:
- "pass": true or false
- "confidence": 0 to 1, how sure you are
- "seen": what is in the photo, at most 12 words
- "reaction": one playful line to the player, at most 20 words. If they failed, give a hint for a better photo.`;
}

export async function judgePhoto(baseUrl, model, quest, imageBase64) {
  const started = performance.now();
  const data = await chat(baseUrl, {
    model,
    stream: false,
    format: VERDICT_SCHEMA,
    options: { temperature: 0 },
    messages: [{ role: "user", content: judgePrompt(quest), images: [imageBase64] }],
  });
  let v;
  try {
    v = JSON.parse(data.message.content);
  } catch {
    throw new Error("Gemma's answer wasn't valid JSON. Try again.");
  }
  return {
    passed: !!v.pass,
    confidence: Math.min(Math.max(Number(v.confidence) || 0, 0), 1),
    seen: String(v.seen ?? "").slice(0, 200),
    reaction: String(v.reaction ?? "").slice(0, 300),
    model,
    ms: Math.round(performance.now() - started),
  };
}

export async function questIntro(baseUrl, model, quest) {
  const data = await chat(baseUrl, {
    model,
    stream: false,
    options: { temperature: 0.9, num_predict: 60 },
    messages: [{
      role: "user",
      content: `You narrate an outdoor adventure game. In ONE short sentence (max 25 words), dramatically announce this quest to the player like a fantasy narrator. Address them as "Adventurer". No emojis, no quotes.\nQuest: ${quest.title}`,
    }],
  });
  return data.message.content.trim().replace(/^["']|["']$/g, "");
}

// Shrink the photo before sending it to the model: faster, and plenty for judging.
export function fileToBase64(file, maxSide = 896) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(img.width * scale);
      canvas.height = Math.round(img.height * scale);
      canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(img.src);
      resolve(canvas.toDataURL("image/jpeg", 0.85).split(",")[1]);
    };
    img.onerror = () => reject(new Error("Couldn't read that image."));
    img.src = URL.createObjectURL(file);
  });
}
