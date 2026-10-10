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

## 2026-10-10 (night) — v2: world-aware quests + full redesign

User feedback on v1 was blunt and fair: location/weather-blind quests, hollow economy, token ElevenLabs use, invisible TabPFN,
generic green look. Rebuilt from PLAN.md.

### Backend (checkpoint 1)
- `context.py`: Open-Meteo (weather, sunset, rain in next 3 h) + Overpass (parks, water, trees, trails, viewpoints, benches,
  cafés within 1.5 km) + Nominatim (area name). Coordinates rounded to 0.01° (~1 km); cached in Mongo (weather 20 min, places 7 days).
  Test cell in central Bengaluru found Cubbon Park Nature Trail, Lotus Pond, Raj Bhavan Gardens etc. 5.6 s cold, 0.03 s cached.
- Quest library: 92 hand-written templates -> 613 quests (params + twists like "with a friend", "a route you've never used").
  Tagged with needs / effort / minutes / time of day / wet-ok / rain-check. Template embeddings (bge-m3) in Atlas for dedupe.
- Eligibility is code, not AI: places present, weather band, daylight, rain coming. Severe weather -> rain-check quests + free freeze.
- TabPFN: classifier scores every eligible quest; we offer easy (highest odds) / sweet spot (~65%) / stretch. Regressor predicts minutes.
  New features: temp, rain, wind, minutes to sunset, distance, effort. 600 synthetic rows (labelled). Fit warmed in background.
- Bug: TabPFN cache missed every time because the key included a random candidate list (60k tokens for 3 loads). Fixed: score all
  eligible quests once per player/cell/hour/weather -> 3 loads = 20k tokens, repeat loads 2.3 s.
- Bug: uvicorn --reload silently kept serving old code after an edit. Turned reload off.
- Economy: Seeds (streak multiplies them), Basecamp (6 slots × 3 tiers), streak freezes, Field Guide cards from Gemma IDs, 14 badges.

### Frontend (checkpoint 2)
- New identity: trail map / outdoor magazine. Paper, ink, signal orange, procedural topographic lines, Archivo condensed + Instrument Sans.
- Real Unsplash photography (hotlinked, free licence). MapLibre v5 + OpenFreeMap tiles (v6 had a worker bug under Vite).
- Screens: landing (+FAQ), 3-check setup (location, local Gemma auto-detected, name), Today (conditions, 3 choices, map, briefing),
  screen-off Expedition, proof, reward reveal, Basecamp (SVG camp that changes per tier and time of day), Field Guide, leaderboard, profile.
- Gemma jobs: personal briefing (real place names, direction, weather), lenient 3-way judge (pass / close / no), species ID.
- Real test runs on `gemma4:12B`: briefing 5 s (prefetched) / 16 s; judging 16–20 s.
  First prompt was too lenient (bird photo for a puddle quest = "close") and mislabelled a bird as "tree". Fixed by defining "close"
  as "right idea but incomplete" and making Gemma name the thing before classifying it. Re-test: puddle -> "no", bird -> pass,
  "Eurasian Blue Tit", kind bird.
- ElevenLabs runtime generation disabled (cap 0) until the pre-made Ranger lines are approved.

## 2026-10-11 (early) — precise location, even landing, Overpass reliability

- User: detected location wasn't accurate. Cause was mostly my own privacy rounding (0.01° ≈ 1.1 km), so distances could be
  ~700 m off. Now: browser high-accuracy position kept to ~1 m in the browser, sent only to measure distances, never stored.
  Weather/map lookups and caches still use the ~1 km cell. Setup shows a map; tapping it moves the pin.
  Same cell, two points: Lotus Pond 767 m (rounded) vs 204 m (exact).
- User: landing "viewports uneven". Hero was 92vh (a strip of the next section peeked in) and sections were 838/570/908 px.
  Now every landing section is exactly one screen (900/900/900/900 at 1440×900), tiles equal height, soft scroll snap.
- Overpass (OSM) is free but flaky: big union query -> 504; mirrors kumi/private.coffee -> 500; after testing -> 429.
  One cold lookup took 186 s with retries. Fix: one small bbox query per category, 2 at a time, retries with back-off,
  run in a background thread (started at setup), partial results cached 10 min, full results 7 days.
  Today screen shows "still mapping" and refreshes once; quests never wait on Overpass.

## 2026-10-11 (night playtest by Nirav) — fixes

- "Still mapping…" for 20 min: a lookup that got most categories but missed one was cached as partial and still flagged
  "loading", so the banner never cleared and the page refreshed every 30 s. Now partial = done; total failure is noted for
  10 min (street + sky quests meanwhile). Area lookup capped at 75 s using 3 grouped Overpass queries.
  Tonight the public Overpass server returned 504 for the entire 75 s window. Photon/Nominatim respond in <1 s but found no
  named parks within ~6 km of the stored spot, which suggests the desktop browser guessed the location from the ISP.
  The setup map's tap-to-move pin is the remedy.
- "Same quests again": at night only 7 of 92 templates were possible in that area, and rerolls excluded quest ids, so the
  same templates came back with different numbers (10/15/20-minute run). Added 30 templates (night, streets, anywhere):
  122 templates -> 782 quests; 151 eligible at night there (was 36). Rerolls now exclude templates, and the three choices
  come from different categories. Test: 4 rerolls -> 12 distinct templates, 0 repeats.
- Leaderboard verified with two separate test players (both appear on week/all/area boards). All-time and area boards now
  list every player, including 0 XP, so new players see themselves straight away.
- Test helpers on NotNirav (marked demo): +600 Seeds, 6 demo Field Guide cards. Remove before submission.
- New logo: a map pin with three grass blades inside, on signal orange; also the favicon.
- Build script reuses old template embeddings (a full rebuild stalled when Ollama kept swapping Gemma and bge-m3).
