# GrassQuest v2: Plan

Status: **proposal, waiting for approval**. Nothing below is built yet.
Deadline: **Sun Oct 12, 12:29 PM IST** (Oct 11, 11:59 PM PDT). The real outdoor test needs daylight on **Sat Oct 11**.

---

## 1. What was wrong with v1 (honest)

| Problem | Why it matters |
|---|---|
| Quests ignore where you are and what the weather is | "Find moving water" in a desert, or "watch the sunset" in a storm. Kills the theme. |
| XP leads nowhere | No currency, nothing to collect, unlock or build. Streaks have no stakes. |
| ElevenLabs is a "read this aloud" button | Nobody clicks it if they can read. Judges would call it a token integration. |
| TabPFN is invisible | It only tweaks an XP number. Nobody would notice if it were gone. |
| Gemma is under-used | It only judges photos. It can see, identify, write and personalize. |
| Model picker and raw Ollama status in the UI | We support one model. That belongs in a requirements checklist and an FAQ. |
| Generic green look, no real imagery | Doesn't feel like a product or make anyone want to go out. |
| Only 41 hand-written quests | Repeats fast. No variety by place, season or type of person. |

---

## 2. The new core idea

**GrassQuest reads your real surroundings and turns them into an expedition.**

When you open it:
1. It finds where you are (browser location, rounded to ~1 km; raw coordinates are never stored).
2. It checks the **weather right now** and the next few hours (Open-Meteo), plus sunrise/sunset.
3. It looks at **what's actually near you** within walking distance (OpenStreetMap): parks, water, trees, viewpoints, trails, playgrounds, benches, cafés with outdoor seating, and so on.
4. **Code** filters the quest library down to quests that are possible right now (no water quest if there's no water nearby, no sunset quest at noon, no long walk in heavy rain or 42°C).
5. **TabPFN** picks the quest in your sweet spot: hard enough to matter, likely enough that you'll actually do it.
6. **Gemma** turns the chosen template into *your* quest using real place names:
   "Head to the park 650 m north. Before the drizzle starts around 5 PM, find three leaves of different shapes."
7. **ElevenLabs** voices a 30–45 s briefing from "the Ranger". You scan a QR code and it plays on your phone while you walk. **The screen stays off.**
8. You come back with a photo. Gemma judges it **leniently** and, if it spotted a bird, plant or tree, **identifies it and adds a card to your Field Guide**.

Heavy weather means no forced outing. You get a "rain check": a short balcony or window quest, or a free streak freeze.

---

## 3. Each partner gets a real job

### Gemma 4 (local, via Ollama) does runtime AI only
| Job | Input → output |
|---|---|
| Personalize the quest | template + nearby places + weather (JSON) → quest text with real place names, distance, timing |
| Judge the proof (lenient) | photo + quest → `pass` / `close enough` (half reward) / `not yet` + a friendly hint |
| Identify what you found | photo → species or object name, a one-line fun fact, rarity guess → **Field Guide card** |
| Write the Ranger's script | quest + context → briefing script (spoken by ElevenLabs) and an after-quest recap |
| Weekly story | your week's completed quests → "Your week outside" journal entry |

**Not Gemma's job** (code does it once, deterministically): weather parsing, filtering quests, XP and currency math, scheduling, map distances.

*My opinion:* the idea of feeding Gemma a map image is tempting, but it would be slower and less accurate. OpenStreetMap already gives exact names, types and distances as text. Gemma reasons over that list much better than over pixels.

### TabPFN (Prior Labs) becomes visible and central
1. **Picks today's quest.** It predicts P(you'll finish) for every eligible quest, and we serve the one in the 55–75% "flow zone". The card says why: "Picked for you: 64% chance, just challenging enough."
2. **Estimates time.** A TabPFN regressor predicts minutes to complete ("~20 min"). That helps people decide to go.
3. **Flags a streak at risk.** It predicts whether you'll be active tomorrow; if not, the Ranger nudges you or offers a streak freeze.
4. **Gets better features.** New inputs: temperature, rain, wind, daylight left, distance to the needed place, weekday/weekend.

Cost: about 2–3 calls per player per session, all inside the free-tier guard we already built (cap 15M of 20M per month).

### ElevenLabs is the interface while you're outside
1. **Expedition briefing (main use).** Gemma writes it, ElevenLabs voices it, and a QR code opens it on your phone, so the screen goes dark and the audio leads you.
2. **The Ranger.** One consistent character voice for briefings, recaps and level-ups. It's a narrator with a personality, not a reading button.
3. **Sound effects API.** Generated **once** by me and saved as files: reward chime, level-up, card reveal, forest ambience for the expedition screen. This uses a second ElevenLabs product properly at near-zero ongoing cost.

Free-tier reality: 10k credits ≈ 40–50 unique briefings a month. Briefings are cached per quest + area + weather band, so repeats are free. **Check hacktoberfest.com/my/promos for ElevenLabs credits**; that would remove the constraint.

### MongoDB Atlas
Game data, plus **Atlas Vector Search** over thousands of quest embeddings (dedupe, and "more like quests you loved"), plus a **geo index** for the area leaderboard.

### Render
Hosts the API and site. **Only after you've seen and approved v2.**

### Sentry (optional, last)
Traces for TabPFN, ElevenLabs and context lookups. First thing to cut.

---

## 4. Quest library: thousands, not 41

- **~300 templates × parameters** (object, colour, count, place type, distance, time of day, season) → **5,000–10,000 concrete quests**. I generate them once, offline, and store them in Atlas with tags and embeddings.
- **Each quest is tagged with what it needs:** `needs: park | water | trees | open_sky | street`, `daylight`, `max_rain`, `temp_range`, `effort: 1–5`, `minutes`, `social: solo | friends`, `proof: photo | light`.
- **More categories:** movement (walk, run, stairs), nature, birds, sky, urban explorer, photography challenges, mindful (sit 10 min, listen and count sounds), social, food outside, seasonal (monsoon, autumn, winter).
- **Proof stays light** (no strict rules, since there's no real-money prize): any honest outdoor photo related to the quest. "Close enough" pays half.
- Gemma rewrites the text at runtime, so even the same template reads differently every time.
- *My opinion:* scraping quests from the web isn't worth it. The licensing is unclear and quality varies. Templates + context + Gemma give more variety *and* more relevance.

---

## 5. Game economy: a reason to come back

| Layer | What it is |
|---|---|
| **XP → level** | Long-term rank (as now, rebalanced) |
| **Seeds (currency)** | Earned per quest; streak multiplies Seeds |
| **Basecamp** | Your camp scene, upgraded with Seeds: tent → cabin → treehouse, campfire, flag, lantern, pet, telescope. Built from **Kenney.nl assets (free, CC0)**. 6 slots × 3 tiers. |
| **Field Guide** | A collectible "Pokédex of your neighbourhood": every bird, tree, flower or bug Gemma identifies becomes a card. Sets: "Birds of your city", "Trees I've met". Rarity tiers. |
| **Streak** | Real stakes: Seed multiplier, and **streak freezes** you buy with Seeds. Bad weather gives a free freeze automatically. |
| **Weekly boss** | Bigger expedition, unique camp item as the reward |
| **Leaderboards** | Your area (city/neighbourhood, from rounded location) + global |
| **Badges** | Kept, but tied to the Field Guide and to weather ("Monsoon Walker", "Golden Hour Hunter") |

---

## 6. Look and feel: complete redesign

- **Drop the green "grass" look.** New direction: **trail map / outdoor magazine.** Warm paper white, ink black, **signal orange** (trail markers and safety gear), topographic contour lines as texture, a bold condensed display font.
- **Real photography:** about 15 curated **Unsplash** photos (free licence) of real people outdoors (running, hiking, sitting in parks, city walks) for the landing page and category headers.
- **Map:** MapLibre + OpenFreeMap tiles (free, no key) showing you, the quest destination and the walking distance.
- **Screens:** Landing (what this is, for judges too) → Requirements checklist (location ✓, Ollama ✓, model ✓, auto-checked, with an FAQ) → **Today** (weather chip, map, quest, odds, time) → **Expedition** (dark screen, QR for audio, timer) → Proof → **Reward reveal** (Seeds counter, card flip for new Field Guide entries) → Basecamp → Field Guide → Leaderboard.
- The model picker goes away. **One supported model, `gemma4:e2b`**, auto-detected. If it's missing, the checklist shows one command.

---

## 7. Tools and services (all free)

| Tool | Use | Key needed? |
|---|---|---|
| Open-Meteo | current weather, hourly forecast, sunrise/sunset | no |
| OpenStreetMap Overpass API | nearby parks, water, trees, trails… (cached per ~1 km cell) | no (fair use) |
| Nominatim | area name for leaderboards and briefings (1 req/s, cached) | no |
| MapLibre GL + OpenFreeMap | map on the Today screen | no |
| Unsplash | real outdoor photography | no (free licence) |
| Kenney.nl | CC0 game assets for Basecamp and items | no (download) |
| Lucide | icons | no |
| ElevenLabs | TTS (Ranger) + Sound Effects | your key (have it) |
| TabPFN | odds + time estimate | your key (have it) |
| Ollama + `gemma4:e2b` | all runtime AI | local |

---

## 8. Timeline (about 40 hours left, including sleep)

| When | What | Done when |
|---|---|---|
| **Tonight (~5 h)** | Context service (location, weather, OpenStreetMap, cache) · quest template library + generator + tags + embeddings · eligibility filter · Gemma personalize / lenient judge / identify · TabPFN with new features + time regressor | API returns a real, local, weather-aware quest for your location |
| **Sat morning (~5 h)** | Full UI redesign · landing · requirements checklist + FAQ · map · Expedition mode · ElevenLabs Ranger briefing + QR + sound effects | You can play the whole loop and it looks like a product |
| **Sat midday (~3 h)** | Seeds, Basecamp (Kenney), Field Guide cards, streak freezes, area leaderboard | You have something to spend on and collect |
| **Sat afternoon (daylight!)** | **Real outdoor test** with the team, logging real numbers, photos and funny failures | Real data for TabPFN + the write-up |
| **Sat night** | Fixes from the test · deploy to Render (**after your OK**) · README · demo video | Live link |
| **Sun morning** | DEV post as a story · final checks · submit before 12:00 IST | Submitted |

**Cut order if we're behind:** Sentry → sound effects → time-estimate regressor → area leaderboard → Basecamp art (keep Seeds + Field Guide).
**Never cut:** location- and weather-aware quests, the lenient Gemma judge + Field Guide, the Expedition briefing, the redesign, the outdoor test, the write-up.

---

## 9. Known limits (stated openly in the write-up)

- Gemma runs on a **computer** via Ollama, so the phone is your camera and audio player, not the judge. Photos move from phone to computer (or we add LAN mode, see the questions).
- Location quality depends on OpenStreetMap coverage. In sparse areas we fall back to generic street and sky quests.
- TabPFN starts on labelled synthetic data plus our outdoor test. That's said openly.

---

## 10. Decisions I need from you

1. **Phone during the outdoor test:** (A) take photos on the phone, move them to the PC after (zero work), or (B) LAN mode, where the phone opens the site on home Wi-Fi and talks to your PC's Ollama (~1 h; location falls back to city search because browsers block location on plain-http LAN pages). **I recommend A + the QR audio briefing.**
2. **Pull `gemma4:e2b`** on your PC (~7 GB) so I can test the model we tell players to use. You only have 12B now.
3. **OK to download** Kenney asset packs (CC0, a few MB) and ~15 Unsplash photos into the repo?
4. **ElevenLabs credits:** can you check hacktoberfest.com/my/promos? Otherwise we live within ~40–50 briefings a month.
5. **Outdoor test:** who's coming, and what time Saturday (sunset in India is around 6 PM, so we need to be out by ~3:30 PM)?
6. **Sentry:** keep as optional-last, or drop it?
