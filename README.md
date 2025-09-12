# 🚀 Project: Automated Bug Reporter (Vision + NLP) for EA Sports FC25

A QA helper that **captures gameplay anomalies**, grabs a **screenshot/short clip**, and **drafts a high‑quality bug report** automatically (title, severity, environment, observed vs. expected, repro steps).

---

## 1) Goals & Success Criteria

* **Goal**: Reduce manual QA effort by auto-detecting visual anomalies and generating draft bug reports.
* **MVP Success (2 weeks)**:

  * Runs locally while FC25 is on screen.
  * Detects **3+ anomaly types** with >80% precision on curated test clips.
  * Produces a structured bug JSON + Markdown summary + screenshot.
  * One‑click export to CSV/JSON and optional Jira/GitHub issue creation.

---

## 2) High-Level Architecture (scalable-by-design)

```
+------------------+        +-------------------+        +------------------+        +---------------------+
|  Capture Agent   |  -->   |  Detector Service |  -->   |  NLP Summarizer  |  -->   |  Reporter Connector |
| (screen/frames)  |        |(vision pipeline)  |        | (LLM/NLP layer)  |        | (Jira/GitHub/CSV)   |
+------------------+        +-------------------+        +------------------+        +---------------------+
         |                           |                            |                          |
         v                           v                            v                          v
   +------------+             +--------------+              +-------------+            +--------------+
   | Local Disk |  <------->  |   Metadata   |  <--------> |  Events DB  |  <------>  |  Web Dashboard|
   |  (media)   |             | (artifacts)  |             | (SQLite/PG) |            | (React/Next) |
   +------------+             +--------------+              +-------------+            +--------------+
```

**Message Bus (optional for scale)**: NATS/Kafka can decouple modules. For MVP we use in‑process queues (asyncio) with the same interfaces.

---

## 3) Core Components & Responsibilities

1. **Capture Agent**

   * Screen capture at 10–30 FPS (configurable) with GPU‑friendly encoding.
   * Rolling buffer (e.g., 10 s) to save pre/post event clips.
   * Emits `FramePacket {frame_id, ts, image, hwnd, hash}`.

2. **Detector Service (Vision)**

   * Modular pipelines (compose detectors):

     * **HUD/Overlay Integrity** (missing textures/NaN colors, alpha glitches).
     * **Flashing/Flicker** (temporal frequency spikes).
     * **Stuck Frame/Animation Freeze** (frame difference < ε for N frames).
     * **Clipping/Out‑of‑bounds** (edge intersection heuristics + optical flow outliers).
     * **Blank/Black Screen** (luma histogram collapse, saturation ≈ 0).
     * **Text/Number OCR sanity** for overlays (score/time gone/NaN).
   * Emits `AnomalyEvent {type, ts, severity, confidence, evidence_refs}`.

3. **NLP Summarizer**

   * Templates → LLM to draft **title**, **observed**, **expected**, **repro steps**, **env**.
   * Pulls context (map/mode/difficulty via OCR or user config).
   * Emits `BugDraft {title, body_md, json, assets}`.

4. **Reporter Connector**

   * Pluggable sinks: **Jira**, **GitHub Issues**, **Linear**, **CSV/JSON export**.
   * Rate‑limits, retries, and dry‑run mode for portfolios.

5. **Web Dashboard (Optional for MVP)**

   * Local React/Next UI to browse events, screenshots, and submit issues.
   * Live event stream + filtering by type/confidence.

6. **Storage**

   * Media: `/data/media/<session>/<event_id>.(png|mp4)`.
   * DB: SQLite for MVP; Postgres for scale.
   * Artifacts: `artifacts/<event_id>/metrics.json`.

---

## 4) Technology Choices

* **Language**: Python 3.11 (OpenCV, PyTorch optional), with type hints.
* **Vision**: OpenCV, NumPy, scikit‑image, pytesseract (OCR, optional).
* **NLP**: Open-source LLM (e.g., `Llama.cpp`/`Olive`/`GPT‑J`) or API backed.
* **App**: FastAPI for service endpoints; Uvicorn for async; Pydantic models.
* **Storage**: SQLite (MVP), Postgres upgrade path; local disk for media.
* **Packaging**: Poetry; Dockerfile + docker‑compose for one‑command run.
* **Testing**: PyTest; synthetic clip generator for anomalies.
* **Telemetry**: Structured logging (JSON), OpenTelemetry hooks (future).

---

## 5) External Datasets for Prototyping

To accelerate development and validate detection logic, we will integrate two public datasets:

1. **Atari Anomaly Dataset (AAD)**

   * Videogame-focused dataset for anomaly detection research.
   * Useful as a domain proxy to train/test detectors for visual freezes, black screens, and odd transitions.
   * Source: [Kaggle AAD](https://www.kaggle.com/datasets/benedictwilkinsai/atari-anomaly-dataset-aad)

2. **Echo+ FPS Game Dataset**

   * Contains \~300K bug-free play observations and \~500K anomalous video segments.
   * Includes anomalies highly relevant to our use case (black screen, texture corruption).
   * Source: [arXiv paper](https://arxiv.org/pdf/2312.08418)

**Implementation Plan:**

* Add a new `datasets/` folder in the repo:

  ```
  datasets/
    atari_aad/
    echo_plus/
    loaders/
      __init__.py
      atari_loader.py
      echo_loader.py
  ```
* Each loader will:

  * Provide standardized access to frames/clips.
  * Map dataset labels → internal `AnomalyEvent.type` values.
  * Export batches for unit/integration tests of detectors.
* Update CI tests to run detectors on sampled dataset clips and assert detection consistency.
* Documentation in `README.md` with links and usage notes.

---

## 6) Data Contracts (Pydantic models)

```python
class FramePacket(BaseModel):
    frame_id: str
    ts: datetime
    image_path: str  # stored frame path for memory safety
    hud_region: tuple[int, int, int, int] | None
    hash: str

class AnomalyEvent(BaseModel):
    event_id: str
    type: Literal["flicker","freeze","blank","hud_glitch","clipping"]
    ts: datetime
    severity: Literal["low","medium","high","critical"]
    confidence: float  # 0..1
    metrics: dict[str, float]
    evidence: list[str]  # paths to images/clips

class BugDraft(BaseModel):
    event_id: str
    title: str
    body_md: str
    json_payload: dict[str, Any]
    assets: list[str]
```

---

## 7) Vision — MVP Heuristics (fast & explainable)

**A. Black/Blank Screen**

* Luma histogram: if ≥95% pixels in first bin (Y < 10) for ≥T ms → `blank`.
* Add saturation histogram check to avoid night scenes false positives.

**B. Freeze/Stuck Frame**

* Per‑frame SSIM or mean absolute difference; if MAD < 0.001 for N consecutive frames (e.g., 1–2 s) while audio power stays > threshold (optional) → `freeze`.

**C. Flicker/Flashing**

* Global mean luminance time‑series; compute FFT on sliding window; strong high‑freq energy spike (> β) → `flicker`.

**D. HUD/Overlay Glitch**

* Template match HUD regions to expected mask (set by calibration step).
* Alpha/NaN color detector: count pixels with near‑magenta checker (common debug color) or out‑of‑gamut values → `hud_glitch`.
* OCR numbers (score/time) – if suddenly `None`/garbled for > X frames → event.

**E. Clipping/Out‑of‑Bounds (Basic)**

* Edge map + optical flow; if a large flow vector field exits screen bounds or objects intersect camera planes unusually long → flag low‑confidence `clipping`.

> Start with A–C (easy, robust), add D, then E as stretch.

---

## 8) NLP Summarization

* **Prompt template** (few-shot):

```
You are a QA assistant. Given anomaly type, metrics, and context, draft a concise game bug report with:
- Title (<80 chars), Severity, Environment
- Observed Behavior, Expected Behavior
- Repro Steps (3–6 steps, imperative voice)
- Attachments (list)
Return Markdown.
```

* **Inputs**: `AnomalyEvent`, HUD OCR (mode, half, minute), user config (platform, build).
* **Outputs**: `BugDraft` with Markdown body + machine‑readable JSON.
* **Fallback**: Rule‑based templates if LLM offline.

---

## 9) Reporter Connectors

* **CSV/JSON**: Always available (portfolio‑safe).
* **Jira/GitHub**: Optional; .env‑driven tokens; dry‑run by default.
* Uniform interface: `submit(draft: BugDraft) -> SubmissionResult`.

---

## 10) Storage & Schema

**SQLite tables**

* `events(event_id, type, ts, severity, confidence, metrics_json, evidence_paths, status)`
* `frames(frame_id, ts, path, hash)`
* `drafts(event_id, title, body_md, json_payload, created_at)`

Folder layout

```
/data
  /media/<session>/<frame_id>.jpg
  /events/<event_id>/screenshot.png
  /events/<event_id>/clip.mp4
  /artifacts/<event_id>/metrics.json
```

---

## 11) Interfaces & Extensibility

* **Detectors are plugins**: register via entry points (`detectors/blank.py`, `detectors/freeze.py`).
* **Pipelines defined in YAML**:

```yaml
pipeline:
  fps: 15
  detectors: [blank, freeze, flicker, hud_glitch]
  thresholds:
    blank.luma_pct: 0.95
    freeze.mad: 0.001
    freeze.frames: 30
```

* **LLM Provider Abstraction**: Local (gguf) or API; same `summarize(event)` signature.

---

## 12) Deployment & Dev

* `docker compose up` spins:

  * `capture` (privileged for screen read), `detect`, `nlp`, `api`, `dashboard`.
* Local mode: single Python process with asyncio queues.
* Cross‑platform: Windows (primary), macOS (recording permission), Linux (X11/Wayland APIs).

---

## 13) MVP Cutlines

* ✅ Heuristics A–D
* ✅ Screenshot + 3‑second pre/post MP4 clip
* ✅ Markdown + JSON bug draft
* ✅ CSV export; local dashboard stub
* ❌ Jira/GitHub connectors (make stubs; wire later)
* ❌ Advanced ML detectors (train later)

---

## 14) Pseudo‑Code (MVP)

```python
# main.py (single-process MVP)
queue_frames = asyncio.Queue()
queue_events = asyncio.Queue()

async def capture_loop():
    while True:
        frame = grab_screen()
        path = save_frame(frame)
        packet = FramePacket(...)
        await queue_frames.put(packet)
        await asyncio.sleep(1/config.fps)

async def detect_loop():
    state = DetectorState()
    while True:
        pkt = await queue_frames.get()
        for det in detectors:
            evt = det.process(pkt, state)
            if evt:
                save_event_assets(evt)
                await queue_events.put(evt)

async def nlp_loop():
    while True:
        evt = await queue_events.get()
        draft = summarize(evt)
        persist_draft(draft)
        export_csv_json(draft)

asyncio.gather(capture_loop(), detect_loop(), nlp_loop())
```

**Freeze detector sketch**

```python
def freeze_detector(pkt, state):
    mad = mean_abs_diff(pkt.image, state.prev_image)
    state.freeze_run = (state.freeze_run + 1) if mad < THRESH else 0
    if state.freeze_run >= FREEZE_FRAMES:
        return AnomalyEvent(type="freeze", confidence=0.9, metrics={"mad": mad})
```

**LLM summarizer sketch**

```python
def summarize(evt):
    tpl = load_prompt_template()
    md = call_llm(tpl, vars(evt))
    return BugDraft(event_id=evt.event_id, title=extract_title(md), body_md=md,
                    json_payload={"type": evt.type, "metrics": evt.metrics},
                    assets=evt.evidence)
```

---

## 15) Example Bug Draft (Markdown)

```
# [Freeze] Gameplay stalls while crowd audio continues
**Severity**: High  
**Environment**: PC, FC25 v25.1.3, Windows 11, RTX 3060, 144Hz  

## Observed
Video frame remains static for ~1.8s while audio proceeds; HUD timer halts.

## Expected
Continuous motion; no stall in render pipeline.

## Repro Steps
1. Launch Kick‑Off mode, Legendary difficulty.
2. Start match and sprint down left wing for ~10s.
3. During corner camera cut, rendering freezes for ~2s.
4. Observe HUD timer stops; crowd audio continues.

**Attachments**: `screenshot.png`, `clip.mp4`  
**Metrics**: `mad=0.0007`, `freeze_frames=28`, `fps=60`
```

---

## 16) Testing Strategy

* **Unit**: detector thresholds, SSIM/MAD calculators, OCR parsing.
* **Synthetic data**: script to generate flicker/blank/freeze sequences.
* **Golden clips**: small curated set with labeled ground truth.
* **Acceptance**: run end‑to‑end; assert one bug draft per injected anomaly.

Metrics to track: precision/recall per detector, false positive rate, median time‑to‑draft.

---

## 17) 2‑Week Build Plan (aggressive)

**Day 1–2**: Repo init, Poetry, FastAPI skeleton, SQLite schema, frame capture (Windows/macOS), rolling buffer, save frames.
**Day 3–4**: Implement detectors A (blank) & B (freeze); event emission; artifact writing.
**Day 5**: Detector C (flicker) + thresholds YAML; baseline metrics logging.
**Day 6**: HUD region calibration + simple HUD glitch detector (template mismatch).
**Day 7**: NLP summarizer (LLM provider interface) + rule‑based fallback; draft Markdown.
**Day 8**: CSV/JSON exporter; file layout; one‑command Docker compose.
**Day 9**: Minimal web dashboard (list drafts, preview media).
**Day 10**: Synthetic anomaly generator + unit tests.
**Day 11**: Golden clip evaluation; tune thresholds; docs/readme polish.
**Day 12**: Optional: GitHub/Jira connector (dry‑run); API hardening.
**Day 13–14**: Bug bash, demo script, record showcase video.

---

## 18) Repository Structure

```
fc25-bugbot/
  app/
    capture/
    detectors/
    nlp/
    reporter/
    api/
    dashboard/
    storage/
    schemas/
    config/
  datasets/
    atari_aad/
    echo_plus/
    loaders/
  tests/
  data/
  scripts/
  docker/
  README.md
  compose.yaml
  pyproject.toml
```

---

## 19) Risks & Mitigations

* **False positives**: start conservative; require 2 corroborating signals (e.g., freeze + HUD halted).
* **OS capture permissions**: document configuration per OS; provide fallback to video‑file mode.
* **LLM cost/latency**: ship rule‑based fallback + local model option.
* **Game TOS/IP**: use local, personal footage; no game asset redistribution.

---

## 20) Roadmap (post‑MVP)

* Train a lightweight classifier on anomaly patches.
* Add **controller telemetry** correlation (input vs. output state).
* Multi‑instance support via message bus.
* Active‑learning loop: reviewer approves/edits drafts → improve prompts.
* Integration tests in CI with headless video fixtures.

---

# Addendum: macOS‑first Implementation Changes (Primary Dev Machine)

### A) Capture & Encoding

* **Capture stack**: Prefer **ScreenCaptureKit** (macOS 12.3+) via `pyobjc` binding; fallback to **Quartz/CGDisplayStream** or `mss` for simple grabs.
* **Run modes**: `screen` (live desktop) and `file` (offline MP4). Select via config.
* **Encoding**: Use **ffmpeg** (via `imageio-ffmpeg`) to write H.264 (`avc1`) reliably on macOS; keep OpenCV `VideoWriter` as fallback.
* **Permissions checklist**: System Settings → Privacy & Security → enable **Screen Recording** for Terminal/Python, **Accessibility** if input sim is added later.

### B) Process Topology (macOS default)

* Host macOS runs **capture** with screen permissions.
* Docker containers run **detect + nlp + api + dashboard**.
* IPC via localhost HTTP/ZeroMQ; configurable in `config/settings.yaml`.

### C) Tooling Bootstrap (Homebrew)

```
brew update && brew install ffmpeg tesseract python@3.11 cmake pkg-config
python3.11 -m pip install poetry
```

### D) Config Keys (new)

```yaml
pipeline:
  mode: screen   # or file
  fps: 15
  transport:
    kind: http   # or zeromq
    endpoint: http://127.0.0.1:8765
encoding:
  writer: ffmpeg # or opencv
  h264_preset: ultrafast
```

### E) Testing (macOS specifics)

* Add a small **capture diagnostic** that renders FPS and verifies permission status.
* CI runs file‑mode tests; a local `make macos-smoke` runs capture → detector on a 3‑second screen sample.

### F) Commit Plan Deltas

* **Commit 1 (init)** unchanged.
* **Commit 4 now**: `feat(capture-macos): ScreenCaptureKit + Quartz fallback + ffmpeg writer`.
* **Commit 8 note**: artifact clip creation prefers ffmpeg on macOS.
* **Docs**: README gets a **macOS setup** section with permissions + Homebrew steps.

### G) Clarification (OS Target)

* **Primary target is now macOS** for active development and demos; Windows supported for gameplay capture; Linux in file‑mode for CI.
