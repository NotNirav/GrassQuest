# Side Quests — Build Notes

Running log of decisions, problems, and fixes. Raw material for the DEV write-up.

## 2026-10-08 — Day 0

### Decision: website (PWA), not a native app
- Team is web-first; one codebase; judges get a link instead of an APK.
- Native Android (LiteRT-LM Kotlin) is the more reliable on-device path, but slower to build. Kept as a fallback only.

### Decision: Gemma 4 E2B instead of Gemma 3n
- Findings from the official docs (checked 2026-10-08):
  - MediaPipe LLM Inference API is **maintenance-only** on web and Android; Google points to LiteRT-LM.
  - LiteRT-LM **JS** is an early preview: **text-only**, and its supported models are Gemma 4 web builds.
  - Gemma 3n E2B web file is 3.04 GB (MediaPipe, maintenance mode).
- Chosen: **Gemma 4 E2B** via **Transformers.js v4 + WebGPU** (`onnx-community/gemma-4-E2B-it-ONNX`, `q4f16`).
  - Supports image + text input in the browser.
  - Download for the vision path ≈ 3.2 GB (decoder 1.52 GB + embed_tokens 1.59 GB + vision encoder 0.1 GB); cached by the browser after first load.
- Target device: average Android phone with 8 GB RAM, Chrome (WebGPU).
- Risk: memory pressure on a phone tab. **Spike first** before building on it.

### Open questions
- Does the Gemma partner prize accept Gemma 4? (Assumed yes — verify on the challenge page.)
- GitHub remote: TBD (user will provide).

### Spike page built (`spike/index.html`)
- Single static page, Transformers.js 4.3.0 from jsDelivr, `Gemma4ForConditionalGeneration`, `q4f16`, WebGPU.
- Photos downscaled to 768px max side before inference.
- Prompt asks for JSON `{pass, confidence, seen, reaction}`; logs load time, time to first token, tok/s.
- Desktop check (Claude desktop browser pane, RTX/Ampere): page loads, WebGPU + shader-f16 OK.
  Storage quota there is only 2.7 GB, under the ~3.2 GB model, so the model can't be cached in that pane.
- Phone results: TODO (fill in after running on a real 8 GB Android phone).

## 2026-10-09 — Pivot: local Ollama, website first

### Decision: drop on-phone inference, use local Ollama
- The phone spike was never run. Asking every player to download ~3 GB into a mobile browser tab felt fragile.
- New plan: players run **Gemma 4 through Ollama on their own computer**. The website talks to `localhost:11434` directly from the browser,
  so **photos never leave the player's machine** and our server never sees them; it only gets the verdict JSON.
- Cost: players must install Ollama and pull a model (`gemma4:e2b`, the lightest Gemma 4 vision tag). Accepted to keep things simple.
- Gotcha: Ollama returns **403 to requests from unknown websites**. Hosted site needs `OLLAMA_ORIGINS=<site url>` on each player's machine.
  The setup screen shows the exact command for Windows/macOS/Linux.
- `spike/` removed (still in git history).

### Stack (chosen)
- Web: React 19 + Vite 8, plain CSS, desktop-first but works at phone width.
- API: Python FastAPI (Python because TabPFN, Sentry, Mongo and ElevenLabs all have good Python clients).
- DB: MongoDB Atlas; falls back to in-memory `mongomock` when `MONGODB_URI` is unset (dev only).
- Embeddings: `bge-m3` via Ollama, generated once by `scripts/seed.py embed`, stored in `quests_embedded.json` and Atlas.

### Game rules
- Base XP: common 50 · rare 120 · legendary 300 · boss 500.
- Multiplier from TabPFN odds p: `0.75 + 1.25 × (1 − p)` (p=1 → 0.75×, p=0 → 2×). Streak bonus +5%/day, max +50%.
- Level L needs `100 × (L−1)²` XP. 11 level titles, "Couch Potato" → "Legend of the Outside".
- 12 badges (Early Bird, Night Owl, Botanist, Underdog = finish a quest you had <30% odds on, …).
- A player gets paid exactly the XP the quest card promised (bug found in testing: the streak ticking up mid-quest changed the payout).

### Vector dedupe
- Cosine similarities across the 45 quests: median 0.59; true near-dupes ~0.78–0.83
  (bird-photo ↔ two-birds 0.81, moving-water ↔ waterfall 0.81). Threshold set to **0.78**.

### TabPFN
- Features: hour, day of week, category, rarity, streak, user attempts, user pass rate (smoothed), quest pass rate (smoothed).
- Label: pass = 1; fail or skip = 0. Rows that were only shown and never resolved are ignored.
- Uses `tabpfn-client` (Prior Labs API), so the Render box stays small. Refit at most every 10 min.
- 300 synthetic rows seeded, labelled `synthetic: true`.

### Test results (real, on this dev machine)
- `gemma4:12B` vision check on a drawn image: 50 s first call (24 s of that is model load), ~12 tok/s.
- In the app, `gemma4:12B` **correctly failed a drawn "leaf" for a bark quest** in 10.0 s:
  "That looks like a digital graphic! Head outside and find a real tree with some texture."
- Bug found: narrator line from an earlier quest could overwrite the current quest's line (race). Fixed by tracking the current offer id.

## 2026-10-10 — Atlas live, TabPFN live, free-tier guards, rename

- **Renamed to GrassQuest** to match the repo. Mongo database name stays `sidequests` (internal only).
- **Atlas:** connected; 45 quests + `quest_embedding_index` (1024-d cosine). Atlas `$vectorSearch` returns the same similarities
  as the local numpy check (bird-photo ↔ two-birds 0.809), so dedupe behaves the same in dev and prod.
- **TabPFN free tier (from Prior Labs docs + our account's usage endpoint):** 5M tokens/day, 20M/month, resets 00:00 UTC / 1st.
  `estimate_cost` says every predict at our size (300–1000 train rows × 8 cols) costs the **10k minimum**, model v3.5.
  -> 500 predictions/day max. Uploads and fits are free.
- **Guard:** caps 3.75M/day + 15M/month hosted (75%), 2.5M + 10M locally (50%). Usage = max(Prior Labs counter, Mongo ledger).
  Hitting a cap or getting a 429 pauses TabPFN until the next reset; the heuristic takes over. Verified all three cutoffs.
- **Fewer calls:** one TabPFN call scores all 45 quests for a player, cached 30 min or until their history changes.
  Rerolls are free. Plus 30 calls/min site-wide and 40/day per player.
- **First real TabPFN call:** 11.5 s (fit + predict), cached repeat 0.02 s. 10k tokens used.
- **ElevenLabs:** free plan does include API access (Developers → API Keys). Guard: ~7k of 10k credits hosted, ~5k locally,
  15 new lines per player per day, cache hits free, only known players can request audio.
