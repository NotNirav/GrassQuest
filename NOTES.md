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
