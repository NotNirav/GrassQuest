# 🌿 GrassQuest — The Complete Architectural & Project Summary

> **Document Purpose:** An exhaustive, end-to-end breakdown of GrassQuest — including what it does, its purpose and philosophy, the original plan vs. evolution, the complete technology stack, system architecture, how every feature was built, and a full file-by-file inventory.

---

## 1. Executive Summary & Purpose

### 1.1 What is GrassQuest?
**GrassQuest** is a real-world, privacy-first outdoor exploration web application built for the **DEV Hacktoberfest Open-Source AI Challenge, Week 1: "Touch Grass"** (October 2026).

Instead of giving players generic, disconnected todo lists, GrassQuest reads the player’s **real-world physical environment** — their hyper-local weather, current daylight / solar phase, and actual nearby amenities within walking distance (parks, trails, trees, ponds, viewpoints, outdoor cafes) — and generates a tailored real-world expedition.

### 1.2 The Core Gameplay Loop
1. **Context Assessment:** The game inspects live local weather (Open-Meteo), sunset timing, and nearby map features (OpenStreetMap Overpass) around the player's Basecamp.
2. **Three-Choice Quest Offer:** Using an AI difficulty model (**TabPFN**), the game scores all possible quests and presents three personalized choices:
   - **Easy win** (highest odds of completion, quick confidence booster)
   - **Sweet spot** (~65% odds — right in the optimal flow state)
   - **Stretch** (harder outdoor challenge with higher rewards)
3. **The Expedition (Screen-Off Mode):** An audio briefing voiced by **The Ranger** (generated with **ElevenLabs**) sets the scene. The player taps "Start Expedition", the UI shifts into an OLED-friendly screen-off expedition timer with a compass bearing, and the player puts their phone in their pocket to go explore the physical world.
4. **Local Proof & On-Device Vision Judging:** The player takes an outdoor photo and returns to their computer. **Gemma 4** runs locally on the player’s computer via **Ollama** (`localhost:11434`). It judges the photo leniently and identifies any plants, birds, trees, or sky phenomena.
5. **Zero-Photo-Leak Privacy:** **The photo NEVER leaves the player's computer.** The backend API only receives the verdict JSON `{ "verdict": "pass" | "close" | "no", "confidence", "seen", "reaction", "identified" }`.
6. **Game Progression & Economy:**
   - **XP** increases long-term player levels (from "Couch Potato" to "Legend of the Outside").
   - **Seeds** (currency multiplied by streaks) are earned to purchase upgrades for a customizable **Basecamp** (shelter, campfire, lighting, flag, companion, gear).
   - Identified nature items unlock collectible cards in the **Field Guide** ("Pokédex of your neighbourhood").
   - **Streak Freezes** protect hard-earned streaks during bad weather or busy days.

---

## 2. Project Evolution: The Plan, The Pivot, and v2

### 2.1 The v1 Concept and Honest Post-Mortem (`PLAN.md`)
GrassQuest began as an MVP with 41 hand-written quests, a plain green visual theme, and basic XP mechanics. The project team conducted a brutally honest post-mortem:
* **Quests ignored surroundings:** Players were asked to find moving water in dry suburbs or watch sunsets during storms.
* **XP led nowhere:** There was no game currency, no shop, no collectibles, and streaks lacked stakes.
* **ElevenLabs was just a "read aloud" button:** Players simply read the card instead of listening.
* **TabPFN was invisible:** It only slightly adjusted an XP number without informing player decisions.
* **Gemma was underutilized:** It only gave pass/fail verdicts on photos without identifying what was seen.
* **Generic design:** A basic green CSS aesthetic that failed to inspire outdoor adventure.

### 2.2 The v2 Master Plan (`PLAN.md` & `NOTES.md`)
To address these issues, the team established a radical v2 blueprint:
1. **Hyper-Local Context Engine:** Integrate Open-Meteo and OpenStreetMap Overpass so quests only trigger if their prerequisite environment actually exists within 2.5 km.
2. **The 3-Choice Flow Zone via TabPFN:** TabPFN became central, predicting both the probability of completion and estimated walk time in minutes.
3. **Audio-First Expedition Experience:** ElevenLabs was transformed into "The Ranger" narrator, producing immersive audio departure briefings and field reactions.
4. **Field Guide Collectibles:** Gemma 4 was tasked with species and nature identification, adding an educational discovery mechanic to proof submissions.
5. **Basecamp Economy:** Introduction of Seeds currency, a 6-slot customizable SVG Basecamp, and streak freezes.
6. **Complete Aesthetic Redesign:** Shifted from "generic green" to a premium **"Trail Map / Outdoor Magazine"** identity: warm paper (`#f3eee4`), deep ink (`#17140f`), signal orange (`#ff5b1f`), procedural topographic elevation lines, and typography inspired by outdoor field manuals (`Archivo` & `Instrument Sans`).
7. **Scale the Quest Library:** Expanded from 41 quests to 248 hand-crafted templates with parameter combinations and gameplay twists, yielding **1,324 concrete quests**.

### 2.3 Chronological Development Log (`NOTES.md`)
* **Day 0 (2026-10-08):** Attempted an in-browser WebGPU + Transformers.js spike for Gemma 4 on mobile. Concluded downloading 3.2 GB into mobile browser tabs was too brittle across devices.
* **Day 1 (2026-10-09):** Pivoted to running Gemma 4 locally via Ollama on the computer. Configured browser-direct calls to `localhost:11434` with `OLLAMA_ORIGINS` CORS configuration.
* **Day 2 (2026-10-10):** Integrated MongoDB Atlas with 1024-dimensional vector search (`template_embedding_index`) using `bge-m3` embeddings for semantic deduplication. Configured free-tier guardrails for TabPFN and ElevenLabs.
* **Day 2 Night:** Implemented the v2 context engine (Overpass API + Open-Meteo), expanded templates, and built the new visual identity.
* **Day 3 (2026-10-11):** Resolved Overpass timeout/504 errors by implementing query grouping (`green`, `water`, `other`), caching cells, and background thread warming. Replaced Nominatim city search with Komoot’s Photon typeahead search. Added high-accuracy MapLibre satellite pin dropping. Pre-generated Ranger audio lines to eliminate runtime TTS costs. Added demo seed datasets.

---

## 3. High-Level System Architecture

```
                               ┌─────────────────────────────────────────────────────────────┐
                               │                    PLAYER'S LOCAL COMPUTER                  │
                               │                                                             │
                               │  Browser (React 19 + Vite 8)        Ollama (Local Engine)   │
                               │  ┌──────────────────────────┐       ┌─────────────────────┐ │
                               │  │ • Today / Quests         │ Photo │ • Gemma 4 Vision    │ │
                               │  │ • MapLibre Map View      ├──────►│   (Lenient Judge    │ │
                               │  │ • Basecamp SVG Scene     │       │    + Field ID)      │ │
                               │  │ • Audio Ranger Briefings │◄──────┤ • bge-m3            │ │
                               │  └─────────────┬────────────┘Verdict│   (Embeddings)      │ │
                               └────────────────┼────────────(JSON)──┴─────────────────────┘ │
                                                │                                            │
                                                │ REST API (Verdicts, User, State)           │
                                                ▼                                            │
┌────────────────────────────────────────────────────────────────────────────────────────────┘
│  FastAPI Backend (Hosted on Render)
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  │ • Quest Eligibility & Selection Filter                                                  │
│  │ • Context Aggregator & Cell Cache (~1 km)                                               │
│  │ • TabPFN Difficulty Classifier & Time Regressor                                         │
│  │ • Game Economy (XP Math, Seeds, Streaks, Freezes, Badges)                               │
│  │ • Free-Tier Guardrails & Usage Rate Limiters                                            │
│  └──────┬──────────────────┬─────────────────┬───────────────────┬───────────────────┬─────┘
└─────────┼──────────────────┼─────────────────┼───────────────────┼───────────────────┼──────
          ▼                  ▼                 ▼                   ▼                   ▼
   MongoDB Atlas        Open-Meteo      OSM Overpass API     Photon / Nominatim    Prior Labs TabPFN
  • Users & Attempts   • Live Temp      • Parks & Water      • Typeahead Search   • P(Completion)
  • 1,324 Quests       • Hourly Rain    • Trees & Trails     • Reverse Geocode    • Estimated Minutes
  • Vector Search      • Solar Sunset   • Viewpoints/Cafes   • Locality Names     • Cold-start fit
```

---

## 4. Complete Technology Stack

| Layer | Technology | Version | Purpose in GrassQuest |
|---|---|---|---|
| **Frontend Framework** | React | `19.3.0` | Declarative UI, state management, screen routing |
| **Frontend Tooling** | Vite | `8.3.4` | Ultra-fast development server and production bundler |
| **Mapping Engine** | MapLibre GL | `5.24.0` | Interactive map rendering for Basecamp and quest routes |
| **Map Tiles & Data** | OpenFreeMap & Esri | N/A | Vector tiles (Liberty style) and high-res satellite imagery |
| **Icons** | Lucide React | `1.48.0` | Clean iconography (compass, flames, coins, weather, tent) |
| **Styling** | Vanilla CSS | CSS3 | Custom design system: warm paper, ink, signal orange, dark mode |
| **Backend Framework**| FastAPI | `0.143.0` | Asynchronous REST API |
| **ASGI Server** | Uvicorn | `0.54.0` | High-performance Python server |
| **Database** | MongoDB Atlas / PyMongo | `4.18.3` | Persistent cloud database with Atlas Vector Search |
| **Dev DB Fallback** | Mongomock | `4.3.0` | In-memory MongoDB clone when `MONGODB_URI` is unset |
| **Local Vision AI** | Gemma 4 (via Ollama) | `e2b` / `12b` | On-device photo proof judge, personal briefer, species ID |
| **Embeddings** | bge-m3 (via Ollama) | N/A | 1024-dimensional quest template semantic embeddings |
| **Tabular ML** | TabPFN Client | `0.6.1` | Prior Labs in-context tabular foundation model (Classifier + Regressor) |
| **Voice & Speech** | ElevenLabs Flash v2.5 | N/A | Voice synthesis for "The Ranger" (pre-generated static clips) |
| **Weather API** | Open-Meteo | N/A | Free, keyless live weather, forecasts, sunrise, and sunset |
| **Geospatial API** | OpenStreetMap Overpass | N/A | Free queries for nearby physical amenities and terrain |
| **Geocoding API** | Photon (Komoot) | N/A | Free locality and building typeahead address search |
| **Telemetry** | Sentry SDK | `2.71.0` | Error reporting and performance tracing across HTTP/ML spans |
| **Cloud Hosting** | Render | Blueprint | Free tier Python web service (API) + static site (Web) |

---

## 5. Detailed Feature Breakdown & Implementation

### 5.1 The Environmental Context Engine ([`server/app/context.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/context.py))
* **Privacy-Preserving Cell Coordinates:** Exact browser GPS coordinates are kept in memory solely to calculate walking distances. External lookups, caches, and storage use a ~1 km cell (`round(lat, 2), round(lon, 2)`).
* **Open-Meteo Weather Integration:** Retrieves temperature, apparent temperature, precipitation, wind speed, WMO weather codes, hourly rain probability for the next 3 hours, and sunrise/sunset times.
  - Classifies conditions into bands: `clear`, `cloudy`, `drizzle`, `rain`, `hot` (>=35°C), `cold` (<=3°C), `windy` (>=30 km/h), `fog`, and `severe`.
  - Determines solar phase: `morning` (first 2.5 hours after sunrise), `day`, `golden` (90 mins before to 30 mins after sunset), and `night`.
* **Resilient OpenStreetMap Overpass Batching:**
  - Categorizes OSM tags into `park`, `garden`, `playground`, `water`, `trees`, `field`, `viewpoint`, `trail`, `bench`, and `cafe`.
  - Grouped into 3 queries (`green`, `water`, `other`) within a 3,000 m bounding box to prevent public Overpass server 504 timeouts.
  - Features a multi-tiered cache: full results cached for 7 days, partial results for 10 minutes, and fallback background thread warming (`warm_places()`).
* **Rain Check Mechanism:** When weather is `severe`, outdoor quests are suspended. The system provides gentle indoor/window quests and automatically issues a free **Streak Freeze**.

### 5.2 Quest Generation & Deduplication ([`server/app/quests.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/quests.py) & [`server/scripts/build_quests.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/scripts/build_quests.py))
* **Combinatoric Expansion:** 248 hand-authored templates across 11 categories expanded with parameter variations and 5 gameplay twists:
  1. *Standard* (no twist)
  2. *With a friend* (+1 effort, +5 min)
  3. *Taking a route you've never used* (+1 effort, +10 min)
  4. *Phone in your pocket until you find it* (+1 effort)
  5. *In under 15 minutes* (+1 effort, speed challenge)
  - Result: **1,324 concrete quests** stored in MongoDB.
* **Deterministic Eligibility Filtering:**
  - `needs`: Quests must only require features verified to exist within 2.5 km.
  - `time`: Matches the solar phase (`day`, `golden`, `night`, `any`).
  - `weather`: Rain-resistant quests during wet weather; heat/cold effort limits.
  - `sky`: Celestial quests require low cloud cover (WMO code <= 2).
* **Atlas Vector Search Deduplication:**
  - Templates are embedded into 1024-dimensional vectors using local `bge-m3`.
  - The API retrieves the player's last 3 days of attempts and runs Atlas `$vectorSearch` with a cosine similarity threshold of `0.80`. Near-duplicate quests are filtered out so challenges remain fresh.

### 5.3 TabPFN Difficulty & Time Prediction ([`server/app/difficulty.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/difficulty.py) & [`server/app/tabpfn_budget.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/tabpfn_budget.py))
* **Tabular Foundation Model Integration:**
  - TabPFN predicts completion probability ($P$) using 13 features: `hour`, `day_of_week`, `category`, `effort`, `base_minutes`, `streak`, `user_attempts`, `user_pass_rate` (Laplace-smoothed), `temperature`, `precipitation_mm`, `wind`, `minutes_to_sunset`, and `distance_to_feature_meters`.
  - A TabPFN Regressor predicts the real duration in minutes displayed on the quest card.
* **The 3-Choice Selection:**
  - **Easy Win:** Highest predicted probability.
  - **Sweet Spot:** Closest to the 65% flow zone.
  - **Stretch:** Hardest challenge with $\ge 15\%$ probability.
  - Each choice is guaranteed to come from a distinct category.
* **Free-Tier Guardrails:**
  - Token caps: 3.75M daily / 15M monthly tokens (75% of Prior Labs limits).
  - Rate limiting: Max 30 calls/min site-wide, max 40 calls/player/day.
  - Batched evaluation: Evaluates all eligible candidate quests in a single TabPFN call, cached for 30 minutes.
  - Fallback Heuristic: When offline or over quota, a physics/effort-based heuristic takes over seamlessly.

### 5.4 Privacy-Preserving Vision & Species ID ([`web/src/lib/gemma.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/lib/gemma.js))
* **Zero Cloud Photo Uploads:** Photos are resized locally on an HTML5 canvas to a max side of 1024px and sent directly to `http://localhost:11434/api/chat` on the user's computer.
* **Lenient Judging:** Gemma evaluates the photo against the quest criteria using structured JSON output schemas:
  - `pass`: Legitimate outdoor photo meeting the quest goals.
  - `close`: Right intention but incomplete (e.g., 2 leaves instead of 3); awards 50% XP and Seeds.
  - `no`: Unrelated subject, screen capture, or fake; provides a friendly hint to try again.
* **Field Guide Identification:** Gemma identifies living organisms or sky features:
  - Generates common name, category (`bird`, `plant`, `tree`, `insect`, `fungus`, `sky`, `animal`), a verified fun fact, and rarity (`common`, `uncommon`, `rare`).
  - Automatically awards collectible Field Guide cards and bonus Seeds upon discovery.

### 5.5 Voice of The Ranger ([`web/src/lib/ranger.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/lib/ranger.js) & [`server/scripts/make_voice.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/scripts/make_voice.py))
* **Zero-Cost Voice Strategy:** Rather than burning ElevenLabs API credits on every page load, 16 situational voice lines were pre-rendered using ElevenLabs Flash v2.5 (`scripts/make_voice.py`) and saved as static MP3 files in [`web/public/voice/`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/public/voice/).
* **Audio Triggers:** Played during key moments:
  - Departure lines customized to live conditions (`go-clear`, `go-rain`, `go-hot`, `go-night`, `go-golden`, `go-morning`, `rain-check`).
  - Outcome reactions (`pass`, `close`, `no`, `level-up`, `new-card`, `streak`, `stretch`).
  - Global audio mute/unmute toggle in the navbar.

### 5.6 Game Economy & Progression ([`server/app/game.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/game.py))
* **Dynamic XP Multiplier:** Quests that are personally harder yield higher rewards:
  $$\text{Multiplier} = 0.75 + 1.25 \times (1 - P)$$
  *(Range: $0.75\times$ for $100\%$ odds up to $2.0\times$ for low odds).*
* **Streak & Seed Economy:**
  - Base Seeds (8 to 60 depending on effort) multiplied by daily streak: $+10\%$ per day up to $+100\%$.
  - Spending Seeds:
    - **Streak Freezes:** Cost 40 Seeds (max 2 held). Automatically consumed when a day is skipped.
    - **Basecamp Upgrades:** 6 slots (Shelter, Fire, Light, Flag, Companion, Gear) with 4 upgrade tiers each (e.g., Bedroll $\rightarrow$ Tent $\rightarrow$ Cabin $\rightarrow$ Treehouse).
* **Level Progression:** Quadratic leveling formula: $\text{Level} = \lfloor\sqrt{\text{XP} / 100}\rfloor + 1$. 11 custom titles ranging from *Couch Potato* to *Legend of the Outside*.
* **14 Unlockable Badges:** Recognizing milestones such as *First Steps*, *Early Bird* (<7 AM), *Night Owl* (>9 PM), *Golden Hour Hunter*, *Monsoon Walker*, *Heat Proof* (>32°C), *Birder*, and *Underdog* (completing a quest with $<30\%$ predicted odds).

### 5.7 User Interface & Visual Design ([`web/src/styles.css`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/styles.css))
* **Trail Map Aesthetic:** Handcrafted CSS utilizing warm paper (`#f3eee4`), deep ink (`#17140f`), signal orange (`#ff5b1f`), and procedural topographic elevation contours generated via SVG (`Topo.jsx`).
* **Map Integration (`MapView.jsx`):** Interactive MapLibre GL map supporting vector street tiles (OpenFreeMap Liberty) and satellite imagery (Esri World Imagery) with dynamic route framing between Basecamp and quest targets.
* **Interactive Basecamp (`CampScene.jsx`):** An SVG canvas reflecting the player's camp upgrades in real time, with skies that automatically shift between morning, day, golden hour, and starry night based on local solar calculations.

---

## 6. Complete File-by-File Inventory

### 6.1 Root Files
* [`README.md`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/README.md): Project overview, architecture diagram, local setup instructions, free-tier compliance tables, and hackathon notes.
* [`PLAN.md`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/PLAN.md): Architectural roadmap and design decisions contrasting v1 shortcomings with the v2 implementation.
* [`NOTES.md`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/NOTES.md): Daily development log documenting experiments, bug fixes, token optimization, and playtest findings.
* [`render.yaml`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/render.yaml): Render Blueprint configuring the Python FastAPI service and React static site.
* [`.gitignore`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/.gitignore): Excludes environment files, virtual environments, node modules, and caches.

---

### 6.2 Backend: `server/`
* [`.env.example`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/.env.example): Template for MongoDB Atlas URI, TabPFN token, ElevenLabs API key, and CORS origins.
* [`requirements.txt`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/requirements.txt): Python dependencies (`fastapi`, `uvicorn`, `pymongo`, `mongomock`, `httpx`, `tabpfn-client`, `sentry-sdk`, `numpy`).

#### `server/app/` (Core Application Package)
* [`app/__init__.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/__init__.py): Package initializer.
* [`app/config.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/config.py): Environment configuration and free-tier threshold definitions.
* [`app/db.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/db.py): Database connection manager supporting MongoDB Atlas with automatic fallback to `mongomock`.
* [`app/main.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/main.py): Primary FastAPI application containing all REST endpoints:
  - `/api/users`: Account creation and profile retrieval.
  - `/api/context`: Aggregates weather, solar phase, and nearby places for a coordinate.
  - `/api/geocode` & `/api/reverse`: Address lookup and pin reverse-geocoding via Photon.
  - `/api/quests/today`: Scored 3-choice quest recommendations.
  - `/api/offers/{id}/accept`, `/verdict`, `/giveup`: Quest state management and verdict validation.
  - `/api/camp/buy` & `/api/freeze/buy`: Economy transactions for Basecamp items and streak freezes.
  - `/api/leaderboard`: Area, weekly, and all-time rankings.
  - `/api/tts`: Runtime voice generation with budget checks.
  - `/api/health`: System status, database type, and ML model diagnostics.
* [`app/context.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/context.py): Context engine fetching and caching Open-Meteo weather and OpenStreetMap Overpass places.
* [`app/quests.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/quests.py): Quest eligibility filters, Atlas Vector Search deduplication, and 3-choice recommendation picker.
* [`app/difficulty.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/difficulty.py): TabPFN classifier and regressor scoring pipeline with heuristic fallbacks.
* [`app/tabpfn_budget.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/tabpfn_budget.py): TabPFN token budget tracker and rate limiter.
* [`app/game.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/game.py): Pure game mechanics: XP/Seed formulas, streak reconciliation, Basecamp specifications, and badge definitions.
* [`app/tts.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/tts.py): ElevenLabs TTS client with MongoDB audio caching.
* [`app/data/quests_v2.json`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/data/quests_v2.json): 1,324 expanded concrete quests.
* [`app/data/templates_v2.json`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/app/data/templates_v2.json): 248 base quest templates with pre-computed 1024-d `bge-m3` embeddings.

#### `server/scripts/` (Build & Maintenance Tools)
* [`scripts/quest_templates.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/scripts/quest_templates.py) & [`scripts/quest_templates_more.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/scripts/quest_templates_more.py): Full catalog of 248 hand-authored quest templates.
* [`scripts/build_quests.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/scripts/build_quests.py): Expands templates into 1,324 concrete quests, computes `bge-m3` embeddings via Ollama, and configures the Atlas Vector Search index.
* [`scripts/make_voice.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/scripts/make_voice.py): Pre-renders the 16 Ranger audio clips using ElevenLabs.
* [`scripts/seed.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/scripts/seed.py): Generates synthetic play attempts (`synthetic: true`) for TabPFN cold-start initialization.
* [`scripts/demo.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/scripts/demo.py): Injects or purges demo leaderboard explorers, Seeds, and Field Guide cards for demonstrations.
* [`scripts/clean_test_users.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/scripts/clean_test_users.py): Cleans up test accounts prefixed with `Test_` or `Explorer_`.

#### `server/tests/` (Verification Suites)
* [`tests/test_api_live.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/tests/test_api_live.py): End-to-end integration tests for all FastAPI endpoints.
* [`tests/test_gemma_live.py`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/tests/test_gemma_live.py): Validates local Ollama Gemma 4 vision judging against real sample images.
* [`tests/test_ui_e2e.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/tests/test_ui_e2e.js): Puppeteer browser automation test validating the onboarding and quest selection flow.
* [`tests/verify_reset.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/server/tests/verify_reset.js): Verifies client-side storage reset behavior.

---

### 6.3 Frontend: `web/`
* [`package.json`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/package.json): Frontend dependencies (`react`, `react-dom`, `maplibre-gl`, `lucide-react`, `vite`).
* [`vite.config.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/vite.config.js): Vite bundler configuration with React plugin.
* [`index.html`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/index.html): HTML root with Google Fonts (`Archivo`, `Instrument Sans`) and map stylesheet links.
* [`.env.example`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/.env.example): Frontend environment configuration (`VITE_API_URL`).

#### `web/public/` (Static Assets)
* [`public/favicon.svg`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/public/favicon.svg): Brand icon featuring a signal-orange map pin with three grass blades.
* [`public/voice/*.mp3`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/public/voice): 16 pre-generated Ranger audio clips (`welcome.mp3`, `go-clear.mp3`, `pass.mp3`, `level-up.mp3`, etc.).

#### `web/src/lib/` (Frontend Utility Services)
* [`src/lib/api.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/lib/api.js): Typed HTTP client interfacing with the backend API.
* [`src/lib/gemma.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/lib/gemma.js): Direct browser-to-Ollama driver for Gemma 4 model detection, briefing generation, photo judging, and species identification.
* [`src/lib/ranger.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/lib/ranger.js): Audio playback manager for pre-rendered Ranger clips.
* [`src/lib/location.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/lib/location.js): Browser geolocation utilities, permission checkers, and bearing calculations.
* [`src/lib/photos.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/lib/photos.js): Curated outdoor photography mappings from Unsplash.
* [`src/lib/settings.js`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/lib/settings.js): LocalStorage persistence manager for user preferences and session data.

#### `web/src/components/` (Reusable UI Elements)
* [`src/components/Logo.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/components/Logo.jsx): Brand logo component.
* [`src/components/Topo.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/components/Topo.jsx): Procedural SVG topographic contour line generator.
* [`src/components/MapView.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/components/MapView.jsx): MapLibre GL wrapper supporting street and satellite imagery, custom pins, and route framing.
* [`src/components/BasePicker.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/components/BasePicker.jsx): Interactive Basecamp selector featuring Photon address search and satellite pin placement.
* [`src/components/CampScene.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/components/CampScene.jsx): Dynamic SVG campsite rendering that evolves across 4 upgrade tiers and shifts according to the local solar phase.
* [`src/components/FieldCard.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/components/FieldCard.jsx): Collectible card component displaying species metadata, fun facts, rarity, and 3D flip animations.
* [`src/components/Faq.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/components/Faq.jsx): Accordion FAQ addressing local Ollama setup, CORS configuration, and mobile workflows.

#### `web/src/screens/` (Application Views)
* [`src/screens/Landing.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/screens/Landing.jsx): Marketing landing page showcasing the value proposition, 3-step loop, open AI architecture, and FAQ.
* [`src/screens/Setup.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/screens/Setup.jsx): Onboarding screen performing 3 validation checks: Basecamp location, local Gemma detection, and explorer handle.
* [`src/screens/Today.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/screens/Today.jsx): Core gameplay hub managing quest selection, route briefings, screen-off expedition timer, photo submission, and reward reveals.
* [`src/screens/Basecamp.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/screens/Basecamp.jsx): Basecamp upgrade shop and streak freeze purchasing.
* [`src/screens/FieldGuide.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/screens/FieldGuide.jsx): Collectible album organizing identified flora, fauna, and sky observations.
* [`src/screens/Leaderboard.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/screens/Leaderboard.jsx): Player rankings filtered by local area, current week, and all-time XP.
* [`src/screens/Profile.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/screens/Profile.jsx): Player statistics, unlocked badges catalog, Basecamp settings, and session controls.
* [`src/App.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/App.jsx): Root frontend orchestrator managing navigation, settings, audio state, and screen transitions.
* [`src/main.jsx`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/main.jsx): React application entry point.
* [`src/styles.css`](file:///d:/Computer%20Programming/Hackathons/Upcomming/Hacktober/Task%20-%20Week%201/web/src/styles.css): Complete vanilla CSS styling system.

---

## 7. Operational Integrity & Free-Tier Guarantees

GrassQuest is designed to run indefinitely on zero-cost infrastructure without risk of unexpected charges or account suspensions:

| Service | Free Tier Allocation | GrassQuest Enforced Boundary | Fallback Behavior |
|---|---|---|---|
| **TabPFN (Prior Labs)** | 5M tokens/day, 20M tokens/month | Max 3.75M/day, 15M/month hosted (75%); 2.5M/10M locally (50%) | Pauses TabPFN calls; seamless fallback to physics/effort heuristic |
| **ElevenLabs** | 10k characters/month | 0 runtime calls in normal play (16 pre-rendered static MP3s) | Static MP3 playback costs 0 credits; runtime fallback uses browser TTS |
| **MongoDB Atlas** | 512 MB shared tier | Minimal storage (~1,500 quest documents + user accounts) | Automatic fallback to `mongomock` in-memory database if URI is unset |
| **Open-Meteo** | 10k calls/day (fair use) | Cached in MongoDB per ~1 km cell for 20 minutes | Serves cached weather data |
| **OpenStreetMap Overpass** | Community fair use | Grouped queries; cached per cell for 7 days | Fallback to sky and street quests if Overpass is busy |
| **Photon Geocoding** | Free, open-source | Debounced typeahead search (280 ms) | Standard manual address entry |
| **Gemma 4 Vision** | Open-weight model | Executes entirely on the user's local hardware via Ollama | Zero cloud hosting or vision inference costs |
| **Render** | Free web service tier | Standard container resources | Sleeps after inactivity, wakes on request |

---

## 8. Summary of Achievements

GrassQuest solves the "Touch Grass" challenge not by building a screen-heavy app, but by building an **invitation to leave the screen behind**:
1. **Hyper-Contextual:** Quests are dynamically aligned with real weather and walking-distance landmarks.
2. **Privacy-Preserving:** Local Gemma 4 vision ensures photos never leave the player's computer.
3. **Scientifically Scaled:** TabPFN tabular intelligence accurately predicts completion probability and walking duration.
4. **Rich Progression:** A rewarding loop powered by Basecamp customization, collectible Field Guide entries, and streak freezes.
5. **Sustainable Architecture:** Designed with strict multi-tiered caching and rate-limiting to operate comfortably within free tiers.
