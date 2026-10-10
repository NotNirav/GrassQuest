// Gemma 4 on the player's own computer (via Ollama). It does only the work that needs AI:
// writing the personal briefing, judging the photo, and naming what it sees for the Field Guide.
// Photos never leave this machine.

export const MIN_MODEL = "gemma4:e2b";
const PREFERRED = ["gemma4:12b", "gemma4:e4b", "gemma4:latest", "gemma4:e2b"];

/** Finds the best installed Gemma 4 model. */
export async function detectGemma(baseUrl) {
  let res;
  try {
    res = await fetch(`${baseUrl}/api/tags`);
  } catch {
    return { status: "offline" };
  }
  if (res.status === 403) return { status: "blocked" };
  if (!res.ok) return { status: "offline" };
  const { models = [] } = await res.json();
  const gemmas = models.map((m) => m.name).filter((n) => /^gemma4/i.test(n));
  if (!gemmas.length) return { status: "missing" };
  const pick = PREFERRED.map((p) => gemmas.find((g) => g.toLowerCase() === p)).find(Boolean) ?? gemmas[0];
  return { status: "ok", model: pick };
}

async function chat(baseUrl, body) {
  const send = (b) => fetch(`${baseUrl}/api/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) });
  let res = await send({ think: false, stream: false, keep_alive: "30m", ...body });
  if (res.status === 400) res = await send({ stream: false, keep_alive: "30m", ...body }); // models without a thinking switch
  if (!res.ok) throw new Error(`Gemma error ${res.status}`);
  const data = await res.json();
  return JSON.parse(data.message.content);
}

/** Loads the model into memory ahead of time so the first real request isn't slow. */
export function warmUp(baseUrl, model) {
  return fetch(`${baseUrl}/api/generate`, { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, prompt: "", keep_alive: "30m" }) }).catch(() => {});
}

// ---------- 1. personal briefing ----------
const BRIEFING_SCHEMA = {
  type: "object",
  properties: { title: { type: "string" }, briefing: { type: "string" }, tip: { type: "string" } },
  required: ["title", "briefing", "tip"],
};

export async function personalize(baseUrl, model, quest, ctx) {
  const facts = {
    quest: quest.title,
    good_proof: quest.proof,
    destination: quest.place ? { name: quest.place.name, distance_m: quest.place.dist_m, direction: quest.place.bearing } : null,
    area: ctx.area?.name || ctx.area?.city || null,
    weather: { temp_c: ctx.weather.temp, sky: ctx.weather.label, rain_expected_at: ctx.weather.rain_soon_at },
    time_of_day: ctx.sun.phase,
    minutes_to_sunset: ctx.sun.minutes_to_sunset,
  };
  return chat(baseUrl, {
    model,
    format: BRIEFING_SCHEMA,
    options: { temperature: 0.8, num_predict: 220 },
    messages: [{
      role: "user",
      content: `You are "the Ranger", the warm, slightly dramatic guide of GrassQuest, a game that gets people outside.
Write the player's quest briefing from these facts (JSON):
${JSON.stringify(facts)}

Rules:
- "title": the SAME action as the quest, stated plainly so the player knows exactly what to do (keep the verb and the object, e.g. "Eat a snack outside, no screens" -> "Grab a snack and eat it outside, screens off"). Add the real destination name if there is one. Max 80 characters. Not a poetic headline.
- "briefing": 2-3 short spoken sentences to the player. Say where to go (name, direction, distance) if there's a destination, and use the weather/time (e.g. rain coming, sunset soon). Don't invent places.
- "tip": max 15 words on what photo to bring back.
No emojis.`,
    }],
  });
}

// ---------- 2 + 3. judge the proof and name what's in it ----------
const VERDICT_SCHEMA = {
  type: "object",
  properties: {
    verdict: { type: "string", enum: ["pass", "close", "no"] },
    confidence: { type: "number" },
    seen: { type: "string" },
    reaction: { type: "string" },
    identified: {
      type: "object",
      properties: {
        name: { type: "string" },
        kind: { type: "string", enum: ["bird", "plant", "tree", "insect", "fungus", "sky", "animal", "none"] },
        fact: { type: "string" },
        rarity: { type: "string", enum: ["common", "uncommon", "rare"] },
      },
      required: ["name", "kind", "fact", "rarity"],
    },
  },
  required: ["verdict", "confidence", "seen", "reaction", "identified"],
};

export async function judge(baseUrl, model, quest, imageBase64) {
  const started = performance.now();
  const v = await chat(baseUrl, {
    model,
    format: VERDICT_SCHEMA,
    options: { temperature: 0.2 },
    messages: [{
      role: "user",
      images: [imageBase64],
      content: `You are the friendly judge of GrassQuest, a casual game that gets people outside. Nobody wins money, so be generous.
Quest: "${quest.title}"
A good photo looks like: ${quest.proof}

Decide:
- "pass": an honest photo that reasonably fits the quest. Framing, blur and lighting don't matter.
- "close": the right idea but incomplete (e.g. 2 leaves instead of 3, a cloudy sky for a stars quest, a pond for a puddle quest).
- "no": the main subject has nothing to do with the quest (even if it's a nice outdoor photo), a screen/screenshot, or obviously not real.
Also:
- "seen": what's in the photo, max 12 words.
- "reaction": one playful line to the player, max 22 words. If not a pass, give a friendly hint.
- "identified": the most interesting living thing or sky feature in the photo. First "name" it with its common name (e.g. "House Sparrow", "Neem tree", "Cumulus clouds"), then set "kind" to what that named thing is (a bird is "bird", a flower is "plant"). If nothing identifiable, empty name and kind "none". "fact": one surprising true fact, max 20 words. "rarity": how unusual it is to spot in daily life.`,
    }],
  });
  return {
    verdict: ["pass", "close", "no"].includes(v.verdict) ? v.verdict : "no",
    confidence: Math.min(Math.max(Number(v.confidence) || 0, 0), 1),
    seen: String(v.seen ?? "").slice(0, 200),
    reaction: String(v.reaction ?? "").slice(0, 300),
    identified: v.identified && v.identified.kind !== "none" && v.identified.name
      ? { kind: v.identified.kind, name: String(v.identified.name).slice(0, 60), fact: String(v.identified.fact ?? "").slice(0, 200), rarity: v.identified.rarity || "common" }
      : null,
    model,
    ms: Math.round(performance.now() - started),
  };
}

// Shrink photos before judging: faster, and plenty of detail.
export function fileToBase64(file, maxSide = 1024) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
      const c = document.createElement("canvas");
      c.width = Math.round(img.width * scale);
      c.height = Math.round(img.height * scale);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(img.src);
      resolve(c.toDataURL("image/jpeg", 0.85).split(",")[1]);
    };
    img.onerror = () => reject(new Error("Couldn't read that image. Try a JPG or PNG."));
    img.src = URL.createObjectURL(file);
  });
}
