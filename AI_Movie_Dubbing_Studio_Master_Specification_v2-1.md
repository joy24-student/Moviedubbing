# AI Movie Dubbing Studio - Master Product & Engineering Specification v2.0

> Python-only Windows desktop edition. Local-first, professional, modular, GPU-aware, non-destructive and resumable.

| PRODUCT & SYSTEM DESIGN SPECIFICATION AI Movie Dubbing Studio Professional, realistic, high-speed, multilingual Windows dubbing workstation built with Python PYTHON  \|  LOCAL AI  \|  LLM ROUTER  \|  GPU ACCELERATION  \|  CINEMA WORKFLOW Architecture target: native desktop workflow, local-first processing, modular AI engines, optional cloud/unofficial LLM providers. Version 1.0  •  August 2026 |
| --- |

CONFIDENTIAL MASTER PRODUCT & ENGINEERING SPECIFICATION

## 1. Document Control

Purpose, audience, boundaries and architectural decisions for the Python-only Windows product.

| Field | Definition |
| --- | --- |
| Product name | AI Movie Dubbing Studio (working title) |
| Target platform | Windows 10/11 desktop |
| Primary language | Python for application and orchestration code |
| UI framework | PySide6 / Qt Widgets, fully driven from Python |
| Media runtime | FFmpeg/FFprobe binaries controlled by Python |
| AI execution | Local GPU models plus pluggable LLM/API providers |
| Database | SQLite for local projects; optional PostgreSQL in future team edition |
| Target users | Creators, dubbing teams, localization studios, independent filmmakers, educational/video publishers |
| Document status | Architecture and implementation blueprint v1.0 |
| Primary objective | Produce professional multilingual dubbing with high realism, controllability and speed |

| DEFINITION OF PYTHON-ONLY  Application logic, desktop UI, orchestration, project engine, workers and integrations are implemented in Python. Native dependencies such as FFmpeg, CUDA, GPU drivers and model runtimes remain external binaries because replacing them with pure Python would reduce performance and reliability. |
| --- |

## Contents at a Glance

A navigational map of the complete architecture and implementation specification.

| Part | Sections | Coverage |
| --- | --- | --- |
| Product strategy | 1–5 | Document control, vision, users and complete feature scope |
| Core architecture | 6–10 | Pipeline, system architecture, Python stack, repository and media ingestion |
| Media intelligence | 11–15 | Scenes, stems, ASR, diarization and character memory |
| Language & providers | 16–18 | Translation, DeepSeek/Gemini/ChatGPT routing and prompt orchestration |
| Performance synthesis | 19–25 | Voice, emotion, timing, lip-sync, mixing, subtitles and multilingual projects |
| Desktop experience | 26–30 | Design system, screens, timeline, database and project storage |
| Execution & quality | 31–37 | Jobs, performance, GPU/VRAM, QC, security, recovery and testing |
| Distribution & operations | 38–41 | Packaging, settings, service contracts and quality presets |
| Delivery roadmap | 42–45 | Phases, milestones, MVP and risk controls |
| Governance & reproducibility | 46–49 | Credentials, artifact provenance, diagnostics and CLI |
| Reference & final decisions | 50–56 | Example workflow, principles, expansion, decisions, readiness, glossary and conclusion |

## 2. Executive Summary

AI Movie Dubbing Studio is a local-first professional Windows application that converts films, episodes, documentaries and other long-form video into synchronized multilingual versions while preserving character identity, emotional delivery, music, effects and visual timing.

The product is intentionally designed as a modular post-production system rather than a single “translate and speak” model. Speech recognition, speaker diarization, translation, voice generation, timing, lip-sync, source separation, mixing, quality control and rendering are separate engines connected through a resumable job graph.

| CORE PRODUCT PROMISE  Import a movie, analyze it once, then create multiple language versions through a professional timeline where every AI decision can be inspected, edited, regenerated and versioned. |
| --- |

### 2.1 Strategic differentiators

• Windows-native professional editing workflow rather than browser-only upload/download.

• Local/offline operation for sensitive or unreleased content.

• Character-centric voice memory across scenes, episodes and seasons.

• Performance-aware dubbing: timing, energy, pitch, emotion, pauses and emphasis are modeled separately from text.

• Selective lip-sync: only expensive shots are visually regenerated.

• Audio stem preservation and cinematic remixing instead of simply replacing the complete soundtrack.

• Multi-provider LLM router supporting DeepSeek, Gemini and ChatGPT-style unofficial endpoints without hard-coding the product to one provider.

• Non-destructive editing, caching, crash recovery and partial re-rendering for long projects.

## 3. Product Vision, Goals and Boundaries

### 3.1 Vision

Create a “DaVinci Resolve for AI dubbing”: a desktop studio where AI accelerates language localization but professional users retain control over translation, acting, voice identity, synchronization, mix and export.

### 3.2 Primary goals

1. Professional output quality suitable for online release and, after human review, high-end media workflows.

2. Fast processing through GPU execution, parallel scene workers, caching and selective re-rendering.

3. Realistic character continuity across an entire project.

4. Multi-language production from one analysis pass.

5. Local-first privacy and optional cloud/provider augmentation.

6. Reliable long-running jobs with checkpointing and crash recovery.

7. A simple one-click mode for beginners and a deep timeline mode for professionals.

### 3.3 Non-goals for V1

• Replacing professional dubbing directors in every high-budget production.

• Claiming guaranteed perfect translation or perfect lip synchronization.

• Supporting every codec/container at first release.

• Training foundational speech or multimodal models from scratch.

• Automating voice cloning without authorization or rights tracking.

## 4. Users and Workflow Personas

| Persona | Need | Typical workflow |
| --- | --- | --- |
| Solo creator | Fast affordable multilingual videos | Import → auto dub → fix flagged lines → export |
| Localization editor | Precise translation and timing control | Analyze → glossary → translate → line edit → regenerate → QC |
| Dubbing director | Consistent character performances | Character bible → voice casting → emotion direction → scene review |
| Audio engineer | Clean stems and broadcast-ready mix | Stem inspect → dialogue process → spatial mix → master |
| Studio administrator | Security, reproducibility, model control | Offline policy → model packages → audit → project archive |
| Developer/integrator | Automated jobs | Local API/CLI → job queue → callbacks/logs → export |

## 5. Complete Feature Scope

#### Project & media

Project creation and templates  •  Drag-and-drop media import  •  FFprobe metadata inspection  •  Proxy generation  •  Autosave and recovery snapshots  •  Project archive/restore  •  Media relinking

#### AI analysis

Language detection  •  Speech activity detection  •  ASR with word timestamps  •  Speaker diarization  •  Scene/shot segmentation  •  Face tracking  •  Speaker-face association  •  Emotion/prosody analysis  •  Audio stem separation

#### Translation

Context-aware translation  •  Duration-aware adaptation  •  Character style profiles  •  Glossary/translation memory  •  Pronunciation dictionary  •  Alternative translations  •  Back-translation checks  •  Multi-language branching

#### Voice

Voice library  •  Authorized voice cloning  •  Voice matching  •  Character voice lock  •  Emotion/prosody transfer  •  Rate/pitch/energy controls  •  Regeneration versions  •  Non-verbal vocal handling

#### Visual

Lip-sync preview  •  Selective shot lip-sync  •  Face visibility confidence  •  Before/after comparison  •  Visual QC

#### Audio

Dialogue/music/SFX stems  •  Room/acoustic matching  •  Noise cleanup  •  Dynamic processing  •  Stereo/spatial positioning  •  Loudness normalization  •  Mastering  •  M&E preservation

#### Editing

Professional timeline  •  Multi-track audio/subtitle  •  Line inspector  •  Waveforms  •  Markers  •  Undo/redo  •  A/B versions  •  Batch fixes  •  Keyboard shortcuts

#### Rendering

Render queue  •  Resume after crash  •  Per-language output  •  Audio-only output  •  Subtitle export  •  MP4/MKV/MOV remux/encode  •  Batch project rendering

#### Operations

Model manager  •  GPU/VRAM dashboard  •  API/provider manager  •  Secrets vault  •  Logs  •  Diagnostics  •  Storage cleanup  •  Update manager

## 6. End-to-End Dubbing Pipeline

```text
SOURCE MOVIE<br>   ↓<br>MEDIA ANALYSIS → PROXY / INDEX<br>   ↓<br>AUDIO EXTRACTION ───────────────┐<br>   ↓                            │<br>SOURCE SEPARATION               │<br>   ↓                            │<br>VAD → ASR → WORD TIMESTAMPS     │<br>   ↓                            │<br>DIARIZATION → CHARACTER MAP     │<br>   ↓                            │<br>SCENE + FACE + EMOTION CONTEXT  │<br>   ↓                            │<br>TRANSLATION / ADAPTATION ← LLM ROUTER<br>   ↓<br>VOICE / PERFORMANCE GENERATION<br>   ↓<br>TIMING ALIGNMENT<br>   ↓<br>SELECTIVE LIP-SYNC<br>   ↓<br>DIALOGUE PROCESSING + M&E REBUILD<br>   ↓<br>AI / RULE-BASED QC<br>   ↓<br>HUMAN REVIEW / REGENERATE<br>   ↓<br>MASTER + EXPORT
```

### 6.1 Analyze once, localize many times

The expensive source-side analysis—shots, speakers, faces, original transcript, timestamps and stems—must be shared by every target language. Each new language creates only translation, generated dialogue, language-specific lip-sync decisions, subtitles and final mixes.

## 7. System Architecture

```text
PySide6 Desktop UI<br>      │<br>      ├── Project Service<br>      ├── Timeline Service<br>      ├── Settings / Secrets<br>      └── Local Event Bus<br>              │<br>       Job Orchestrator<br>      ┌───────┼──────────────┐<br>      │       │              │<br> Media Worker│         AI Worker Pool<br> (FFmpeg)    │        ┌──────┼──────────────┐<br>             │        ASR  Translation  Voice/Lip<br>             │          \       \|          /<br>             └────────── Cache + Artifact Store<br>                         │<br>                      SQLite
```

### 7.1 Architectural rules

• UI never performs heavy AI inference directly.

• Every long operation is a cancellable job with progress and checkpoint state.

• All generated outputs are immutable versioned artifacts; user edits create new versions.

• Provider-specific code lives behind adapter interfaces.

• Every engine emits structured metrics, logs and confidence values.

• A project can reopen without re-running completed stages.

## 8. Python Technology Stack

| Layer | Recommended technology | Reason |
| --- | --- | --- |
| Desktop GUI | PySide6 + Qt Widgets | Mature native desktop UI, docking, graphics views, multimedia integration, Python bindings |
| Async UI tasks | asyncio + qasync | Keep UI responsive while coordinating jobs |
| Process isolation | multiprocessing / subprocess | Separate crash-prone FFmpeg and GPU workers |
| Validation/config | Pydantic + pydantic-settings | Typed settings and job payloads |
| Database | SQLite + SQLAlchemy/SQLModel | Reliable local structured project state |
| Media | FFmpeg + FFprobe via subprocess | Industry-standard demux/decode/encode/mix |
| Video/audio arrays | NumPy, OpenCV, soundfile, librosa | Frame/audio processing and features |
| AI runtime | PyTorch + CUDA; optional ONNX Runtime | GPU inference and optimized deployment paths |
| Waveform/timeline | PyQtGraph + custom QGraphicsView | Fast interactive waveform and timeline rendering |
| Logging | structlog/loguru + JSON log files | Human-readable and machine-diagnosable logs |
| Testing | pytest + pytest-qt | Unit, service and GUI testing |
| Packaging | Nuitka or PyInstaller standalone | Distribute a Windows application without requiring user Python |
| Installer | Bundled installer wrapper | Install runtime, shortcuts, file associations and prerequisites |

| COMMERCIAL LICENSING  Before shipping commercially, verify the licenses and model-use terms for every local model and dependency. Treat model licensing as a release gate, not an afterthought. |
| --- |

## 9. Proposed Repository Structure

```text
ai_dubbing_studio/<br>├─ app.py<br>├─ ui/<br>│  ├─ main_window.py<br>│  ├─ dashboard/<br>│  ├─ editor/<br>│  ├─ timeline/<br>│  ├─ translation/<br>│  ├─ voice_studio/<br>│  ├─ mixer/<br>│  ├─ qc/<br>│  ├─ render_queue/<br>│  ├─ model_manager/<br>│  └─ settings/<br>├─ core/<br>│  ├─ project.py<br>│  ├─ events.py<br>│  ├─ jobs.py<br>│  ├─ artifacts.py<br>│  ├─ cache.py<br>│  └─ exceptions.py<br>├─ media/<br>│  ├─ probe.py<br>│  ├─ ffmpeg.py<br>│  ├─ proxy.py<br>│  ├─ stems.py<br>│  └─ render.py<br>├─ ai/<br>│  ├─ asr/<br>│  ├─ diarization/<br>│  ├─ vision/<br>│  ├─ emotion/<br>│  ├─ translation/<br>│  ├─ voice/<br>│  ├─ lipsync/<br>│  └─ qc/<br>├─ providers/<br>│  ├─ base.py<br>│  ├─ router.py<br>│  ├─ deepseek_adapter.py<br>│  ├─ gemini_adapter.py<br>│  └─ chatgpt_adapter.py<br>├─ db/<br>├─ workers/<br>├─ models/<br>├─ resources/<br>├─ tests/<br>└─ packaging/
```

## 10. Media Ingestion and Project Preparation

### 10.1 Import workflow

1. Validate file and permissions.

2. Probe streams with FFprobe.

3. Record source fingerprint and media hashes.

4. Create lightweight edit proxy if source is 4K/8K or high-bitrate.

5. Extract reference audio in a lossless working format.

6. Discover embedded subtitles, chapters and language tags.

7. Generate thumbnail strip and waveform cache.

8. Create source artifact records; never overwrite originals.

### 10.2 Supported first-release inputs

Prioritize MP4, MKV, MOV and common H.264/H.265/AV1 video streams plus AAC, PCM, AC-3/E-AC-3 where legally/licensing-wise appropriate in the bundled FFmpeg build. Unsupported streams should be transcoded into a safe internal mezzanine format.

### 10.3 Proxy policy

Editing preview uses proxies; final render references original frames. This keeps timeline interaction fast while preserving output quality.

## 11. Scene, Shot and Visual Analysis

#### Scene segmentation

Identify logical scene boundaries from shot changes, audio continuity and optional LLM-assisted context.

#### Shot detection

Detect camera cuts and build a shot index to avoid unnecessary lip-sync across unrelated frames.

#### Face detection/tracking

Assign stable face track IDs across each shot.

#### Active-speaker cues

Combine diarization timing with mouth movement and face visibility.

#### Visibility scoring

Classify speaking shots as close-up, medium, tiny face, occluded, off-screen or back-facing.

#### Lip-sync priority

Only high-visibility speaking shots receive expensive visual regeneration.

| PERFORMANCE OPTIMIZATION  A feature film may contain thousands of shots. Visual analysis should output metadata first; lip-sync rendering must be scheduled only for shots where it materially improves perceived quality. |
| --- |

## 12. Audio Intelligence and Stem Separation

### 12.1 Preferred source hierarchy

1. Studio-supplied M&E (Music & Effects) track — best quality.

2. Dialogue-isolated production stems — excellent.

3. AI source separation from a mixed master — fallback.

### 12.2 Internal stems

• Dialogue

• Music

• Effects

• Ambient/noise bed

• Optional vocals/non-dialogue human sounds

### 12.3 Processing rules

Preserve the original M&E whenever possible. Avoid aggressive source separation that damages music or effects. Store stem confidence and enable manual replacement. Use lossless working audio during editing; encode only during final export.

## 13. Speech Recognition and Timing Model

### 13.1 Required transcript granularity

| Utterance<br>├─ speaker_id<br>├─ start_ms / end_ms<br>├─ source_text<br>├─ language<br>├─ confidence<br>├─ emotion/prosody summary<br>└─ words[]<br>   ├─ text<br>   ├─ start_ms / end_ms<br>   └─ confidence |
| --- |

### 13.2 Local ASR strategy

Use a fast local Whisper-compatible implementation or another licensed speech engine with word-level alignment. Keep ASR model selection configurable by VRAM, source language and quality mode. For very long media, chunk by VAD/scene boundaries and merge with deterministic timestamps.

### 13.3 Correction workflow

ASR text is editable before translation. Corrected lines are locked against accidental overwrite unless the user explicitly re-runs recognition.

## 14. Speaker Diarization and Character Identity

### 14.1 Two-layer identity model

A speaker cluster is an acoustic identity; a character is a project-level editorial identity. The editor can merge/split speaker clusters and map them to named characters.

| Object | Examples of stored data |
| --- | --- |
| Speaker cluster | Embedding, source segments, confidence, acoustic stats |
| Character | Display name, role, face tracks, source speaker IDs, language style |
| Voice profile | Authorized reference, voice embedding/model, target-language settings |
| Performance profile | Pitch range, pace, energy, emotion tendencies |
| Continuity rule | Keep voice assignment stable across scenes/episodes |

## 15. Character Bible and Project Memory

For long-form narrative consistency, each project maintains a character bible. The translation and voice engines retrieve relevant character data for every line instead of treating lines independently.

### 15.1 Character bible fields

• Name and aliases

• Narrative role

• Age/voice style descriptors

• Relationship notes

• Formality level

• Catchphrases and terminology

• Pronunciation preferences

• Source voice samples

• Authorized target voice profile

• Accent/style per target language

• Known emotional range

• Do-not-change notes

### 15.2 Scene memory

For each scene, maintain a compact summary, participating characters, location, emotional tone, previous scene transition and terminology. This context is passed to translation/QC prompts within token limits.

## 16. Translation and Adaptation Engine

### 16.1 Translation is a constrained writing problem

A professional dub translation must preserve meaning, character intent and plot terminology while fitting a time window and sounding natural when spoken. Literal translation alone is insufficient.

### 16.2 Multi-pass translation pipeline

1. Semantic translation: preserve meaning and references.

2. Character adaptation: match formality, personality and age.

3. Cultural localization: adapt idioms without changing story intent.

4. Timing adaptation: shorten/expand to target duration.

5. Pronunciation pass: enforce names and specialized terms.

6. Back-check/QC: compare source meaning against final target text.

### 16.3 Duration score

Estimate target spoken duration from language-specific speaking rate and punctuation, then compare against source timing. Lines outside configured tolerance are automatically offered shorter/longer alternatives.

## 17. DeepSeek + Gemini + ChatGPT Provider Architecture

| CRITICAL RELIABILITY RULE  Because you plan to use unofficial endpoints, the application must treat every provider as replaceable and untrusted for availability. No provider should own project state, prompts or business logic. |
| --- |

### 17.1 Provider interface

```text
class LLMProvider(Protocol):<br>    async def health_check(self) -> ProviderHealth: ...<br>    async def complete(self, request: LLMRequest) -> LLMResponse: ...<br>    async def stream(self, request: LLMRequest) -> AsyncIterator[Chunk]: ...<br>    def capabilities(self) -> CapabilitySet: ...
```

### 17.2 Recommended roles

| Provider | Primary roles | Fallback behavior |
| --- | --- | --- |
| DeepSeek adapter | Translation alternatives, long-form reasoning, terminology analysis, cost-efficient review | Route to Gemini/ChatGPT adapter or local model |
| Gemini adapter | Scene/context interpretation, multimodal-style reasoning where endpoint supports it, translation review | Fallback to ChatGPT/DeepSeek |
| ChatGPT adapter | Dialogue naturalization, structured QC, director-style rewrite, conflict resolution | Fallback to Gemini/DeepSeek |
| Local LLM adapter | Offline translation/rewrite, privacy mode, emergency fallback | Quality mode can escalate to cloud provider when permitted |

### 17.3 Router scoring

Select provider by capability, latency, recent failure rate, token/window limits, project privacy policy, target language, estimated cost and user priority. Maintain a circuit breaker: temporarily stop routing to providers that repeatedly fail or return malformed data. Keep the adapter contract compatible with future official APIs. The Provider Manager should expose health-test status, latency, recent failures and supported capabilities. Log request metadata and hashes rather than sensitive prompt contents by default.

### 17.4 Unofficial API safeguards

• Do not embed account cookies or raw credentials in source code.

• Encrypt provider secrets at rest using Windows-protected credentials or a local encrypted vault.

• Never upload original movie media unless the user explicitly enables it and the endpoint requires it.

• Use strict timeouts, response schema validation, retries with jitter and provider cooldowns.

## 18. Prompt and Context Orchestration

### 18.1 Context package per utterance

| SYSTEM POLICY<br>PROJECT LANGUAGE RULES<br>CHARACTER PROFILE<br>SCENE SUMMARY<br>GLOSSARY / TRANSLATION MEMORY<br>PREVIOUS 2-5 LINES<br>CURRENT SOURCE LINE + TIMING<br>NEXT 1-3 LINES<br>TARGET CONSTRAINTS<br>EXPECTED JSON SCHEMA |
| --- |

### 18.2 Structured output

Require JSON/Pydantic outputs containing translation, alternatives, estimated duration, style notes, terminology decisions, warnings and confidence. Reject malformed responses and retry with a repair prompt rather than allowing arbitrary text into project state.

### 18.3 Prompt versioning

Every production prompt has an ID and version. Store the prompt version used to generate each translation so results are reproducible and migrations can be audited.

## 19. Voice Generation and Voice-Cloning Subsystem

### 19.1 Voice engine abstraction

Do not hard-code one TTS/voice-cloning library. Define a local VoiceEngine interface supporting synthesis, reference-conditioned generation, language support, emotion controls, streaming/preview and deterministic seeds where available.

### 19.2 Candidate local engines

Evaluate commercially compatible multilingual voice-cloning/TTS engines such as XTTS-family, F5-style TTS, GPT-SoVITS-style systems or other actively maintained models. Model selection must be a configuration package because licenses and capabilities can change. Verify commercial terms before distribution.

### 19.3 Voice generation inputs

• Target text

• Target language

• Character voice profile

• Reference audio if authorized

• Emotion label/intensity

• Target duration

• Pitch/energy constraints

• Scene/acoustic profile

• Seed/version metadata

### 19.4 Voice rights

Voice cloning must require an authorization record. The project stores owner/actor reference, permission status, allowed project/languages, expiry/revocation and audit notes.

## 20. Emotion, Prosody and Performance Transfer

Separate “who is speaking” from “how the line is performed”. A realistic dub needs voice identity plus performance characteristics.

| Feature | Signal / behavior |
| --- | --- |
| Emotion | Neutral, happy, sad, angry, fear, surprise, whisper, shout, etc. |
| Prosody | Pitch contour, stress, rhythm, pause placement |
| Energy | RMS/intensity curve relative to scene |
| Pace | Syllables/words per second and local accelerations |
| Breath/non-verbal | Sighs, gasps, laughs, cries, coughs when appropriate |
| Director control | More/less intensity, slower/faster, softer/louder, alternate delivery |

### 20.1 Performance transfer strategy

Extract features from the original utterance, normalize them relative to the source character, then map supported controls into the selected target voice engine. Unsupported attributes become advisory metadata for regeneration/QC.

## 21. Timing Alignment and Duration Control

### 21.1 Priority order

1. Adapt translation wording.

2. Adjust pauses and phrasing.

3. Ask voice model for target duration/rate if supported.

4. Apply small high-quality time-stretch corrections.

5. If still mismatched, flag for review instead of extreme speed changes.

### 21.2 Timing metrics

Store source duration, synthesized duration, absolute delta, relative delta, word density, leading/trailing silence and overlap with neighboring speakers. Display these as color-coded indicators in the editor.

## 22. Lip-Sync and Visual Dubbing

### 22.1 Two-tier engine

| Mode | Purpose | Behavior |
| --- | --- | --- |
| Preview | Interactive editing | Lower-cost model/resolution; regenerate selected shot quickly |
| Final | Cinema render | High-quality model only on selected/visible speaking shots |

### 22.2 Shot eligibility

• Speaker face visible

• Face size above threshold

• Mouth not heavily occluded

• Shot duration within model limits

• Confidence that face matches active speaker

• No manual “do not alter” lock

### 22.3 Failure fallback

If lip-sync output has visual artifacts, keep the original shot and retain the dubbed audio. Visual AI must never block completion of the audio dub.

## 23. Dialogue Processing, Acoustic Matching and Mixing

### 23.1 Dialogue chain

| Generated Dialogue<br> → De-noise / cleanup if required<br> → EQ / tonal match<br> → Compression / level shaping<br> → De-esser<br> → Room / reverb matching<br> → Spatial pan / distance<br> → Mix with M&E<br> → Loudness / true-peak control<br> → Master |
| --- |

### 23.2 Acoustic scene profile

For each scene or utterance, store room type, estimated reverberation, noise floor, spectral tilt and spatial placement. Users can override presets such as studio, bedroom, hall, street, vehicle, phone/radio and exterior.

### 23.3 Channel policy

V1 may focus on stereo while preserving original multi-channel tracks for pass-through. A later professional audio module can support explicit 5.1/7.1 dialogue routing and deliverables.

## 24. Subtitle and Caption Engine

• Generate SRT, VTT and ASS.

• Maintain original and translated subtitle tracks.

• Optional speaker labels.

• Subtitle timing derived from edited dialogue segments.

• Line-length and reading-speed QC.

• Import existing subtitle as ASR hint or translation source.

• Burn-in or selectable embedded subtitle export.

## 25. Multi-Language Project Model

```text
Project<br>├─ Source analysis (shared)<br>│  ├─ scenes / shots<br>│  ├─ source transcript<br>│  ├─ speakers / characters<br>│  ├─ faces<br>│  └─ stems<br>└─ Localizations<br>   ├─ Bengali<br>   │  ├─ translations<br>   │  ├─ voices<br>   │  ├─ subtitles<br>   │  └─ mix/render<br>   ├─ Hindi<br>   └─ Spanish
```

This structure minimizes repeated computation and allows a studio to compare localization progress language by language.

## 26. Desktop UI and Design System

### 26.1 Visual direction

Dark professional workstation aesthetic with high information density, strong typography, dockable panels and accent colors for AI state: blue = information, green = pass, amber = review, red = failure, purple = AI-generated/variant.

### 26.2 Main editor layout

```text
┌ Project/Media ┬──────── Video Preview ────────┬ Inspector ┐<br>│ scenes        │                                │ character │<br>│ characters    │            PLAYBACK            │ text      │<br>│ languages     │                                │ AI/QC     │<br>├───────────────┴────────────────────────────────┴───────────┤<br>│ V1 Original Video                                          │<br>│ V2 Lip-sync Overlay                                        │<br>│ A1 Source Dialogue                                         │<br>│ A2 Dub Dialogue                                            │<br>│ A3 Music  A4 Effects  A5 Ambient                           │<br>│ S1 Source Subtitles  S2 Target Subtitles                    │<br>└────────────────────────────────────────────────────────────┘
```

### 26.3 Accessibility and usability

• Keyboard-first editing

• Resizable/dockable panels

• High-DPI support

• Color plus icons/text—never color alone

• Undo/redo for all destructive edits

• Background rendering without blocking edit operations

• Visible auto-save and recovery state

## 27. Complete Screen Catalog

| Screen | Purpose |
| --- | --- |
| Dashboard | Recent projects, create/import, system health, GPU/VRAM, model readiness. |
| New Project Wizard | Source file, target languages, quality preset, privacy mode, storage. |
| Media Inspector | Streams, codecs, audio tracks, subtitle tracks, proxies, technical warnings. |
| Analysis Center | Progress for ASR, stems, diarization, scene/face analysis. |
| Main Timeline Editor | Video preview, tracks, utterances, markers, editing and AI actions. |
| Translation Studio | Source/target text, context, glossary, alternatives, timing score. |
| Character Studio | Character identity, faces, source voices, notes and target voice assignments. |
| Voice Studio | Voice preview, authorization, cloning reference, emotion and performance controls. |
| Pronunciation Studio | Lexicon, phonetic overrides, name/term testing. |
| Lip-Sync Studio | Shot eligibility, before/after preview, model selection and re-render. |
| Audio Mixer | Stem levels, dialogue processing, room presets, pan, master meters. |

### 27.1 Screen Catalog — Continued

| Screen | Purpose |
| --- | --- |
| Subtitle Studio | Subtitle text/timing/style/import/export. |
| Quality Control | Timeline heatmap, issue list, scores, auto-fix actions. |
| Render Queue | Jobs, priority, GPU assignment, progress, pause/resume/cancel. |
| Export Center | Container, codec, audio tracks, subtitles, naming and deliverables. |
| Model Manager | Installed models, size, VRAM needs, load/unload, update/remove. |
| Provider Manager | DeepSeek/Gemini/ChatGPT adapters, status, credentials, rate/failure stats. |
| Hardware Monitor | CPU/GPU/RAM/VRAM/disk, temperature if available, worker state. |
| Storage & Cache | Project size, cache cleanup, model locations, temp space. |
| Settings | General, appearance, performance, AI, audio, privacy, updates, shortcuts. |
| Diagnostics | Logs, crash reports, dependency checks, FFmpeg/GPU/model tests. |
| About & Licensing | App version, dependency/model licenses, acknowledgements. |

## 28. Timeline and Editing Model

### 28.1 Track types

• V1 source video

• V2 generated lip-sync shot overlays

• A1 source dialogue

• A2 target dialogue

• A3 music

• A4 effects

• A5 ambience/foley

• S1 source subtitles

• S2 target subtitles

### 28.2 Utterance actions

Edit translation; split/merge utterance; change speaker; assign character; regenerate voice; change emotion; match duration; preview source/dub; lock line; mark approved; request lip-sync; restore earlier version.

### 28.3 Non-destructive edits

The timeline references artifacts and edit decisions. Original media and prior generations remain untouched. Undo/redo modifies the edit decision graph, not source files.

## 29. Local Database and Data Model

| Entity | Purpose |
| --- | --- |
| projects | Project metadata, source paths, settings, state |
| media_assets | Source/proxy/stem/render files and hashes |
| scenes | Scene boundaries and summaries |
| shots | Shot boundaries and visual metadata |
| utterances | Timed speech segments and source text |
| words | Word timestamps/confidence |
| speaker_clusters | Diarization identities/embeddings |
| characters | Editorial identities and continuity settings |
| face_tracks | Tracked faces per shot |
| speaker_face_links | Association confidence |
| localizations | Target language configuration/status |
| translations | Versioned target text and provenance |
| glossary_terms | Term rules and pronunciations |
| voice_profiles | Voice engine/config/reference metadata |
| voice_authorizations | Consent/rights state |
| voice_generations | Generated audio versions and metrics |
| lipsync_generations | Generated shot variants and QC |
| mix_versions | Audio mix settings and outputs |
| qc_issues | Issues, severity, status, auto-fix history |
| jobs | Job graph nodes and checkpoint state |
| artifacts | Immutable generated files and checksums |
| providers | Endpoint configuration/capability/health |
| model_packages | Local model inventory |
| audit_events | Important security/editorial actions |

## 30. Project File and Storage Layout

```text
ProjectName.aidub/<br>├─ project.db<br>├─ project.json<br>├─ source/          # references / optional managed copy<br>├─ proxy/<br>├─ thumbnails/<br>├─ waveforms/<br>├─ stems/<br>├─ transcripts/<br>├─ localizations/<br>│  ├─ bn-BD/<br>│  │  ├─ generated_voice/<br>│  │  ├─ lipsync/<br>│  │  ├─ subtitles/<br>│  │  └─ mixes/<br>│  └─ hi-IN/<br>├─ cache/<br>├─ renders/<br>└─ logs/
```

Use content hashes for cache keys and artifact deduplication. Project portability should support “collect project” to copy external source media into an archive.

## 31. Job Orchestration and Worker Design

### 31.1 Job states

QUEUED → PREPARING → RUNNING → PAUSED/CANCELLED/FAILED → COMPLETED. A failed job records retry count, checkpoint, error category and diagnostic context.

### 31.2 DAG dependencies

```text
AnalyzeMedia<br> ├─ ExtractAudio<br> │   ├─ SeparateStems<br> │   └─ ASR → Diarize → CharacterMap<br> └─ SceneDetect → FaceTrack<br>                    ↓<br>             Translate(language)<br>                    ↓<br>             GenerateVoice<br>                    ↓<br>             AlignTiming<br>               ┌────┴────┐<br>               │         │<br>            LipSync     MixAudio<br>               └────┬────┘<br>                    QC<br>                    ↓<br>                  Render
```

### 31.3 Local scheduler

Use an in-process scheduler for metadata/short tasks and isolated worker processes for GPU/media workloads. Heavy GPU models should stay warm in dedicated workers to avoid repeated load time.

## 32. Performance and Speed Architecture

### 32.1 Rules for fastest practical processing

1. Chunk by scene/utterance, not whole movie.

2. Run independent CPU/GPU tasks concurrently.

3. Cache every deterministic intermediate.

4. Keep frequently used models resident in VRAM when capacity permits.

5. Batch ASR/embedding/TTS tasks when models support batching.

6. Use proxies for preview and originals only for final output.

7. Skip lip-sync for invisible/small/off-screen faces.

8. Remux video when only audio/subtitles change; avoid unnecessary video re-encode.

9. Regenerate only changed utterances and dependent artifacts.

10. Use mixed precision/quantization only after quality benchmarking.

### 32.2 Performance modes

| Mode | Design |
| --- | --- |
| Eco | CPU-friendly, smaller models, lower worker count, pause heavy GPU on battery |
| Balanced | Default quality and concurrency |
| Performance | High GPU utilization, more parallel tasks, warm models |
| Maximum | Aggressive GPU scheduling for desktop workstations |
| Private/Offline | No cloud provider use; local models only |

## 33. GPU and VRAM Management

The scheduler maintains a model registry with estimated VRAM requirements, currently resident models and active job reservations. Before starting a job it checks free VRAM and chooses load/unload/CPU fallback/queue behavior.

### 33.1 Example policy

| 8 GB VRAM:<br> ASR → unload → Voice → unload → LipSync<br><br>24 GB VRAM:<br> Keep ASR + Voice resident; schedule LipSync in remaining VRAM<br><br>2 GPUs:<br> GPU0 = ASR/Voice<br> GPU1 = LipSync/vision |
| --- |

## 34. AI Quality-Control System

### 34.1 Quality dimensions

| Dimension | Example checks |
| --- | --- |
| Transcription | Low confidence, missing speech, wrong language |
| Speaker | Speaker switches, inconsistent character map |
| Translation | Meaning loss, terminology conflict, unnatural wording |
| Timing | Overrun/underrun, overlap, long silence |
| Voice | Wrong character, pronunciation, artifacts, emotion mismatch |
| Lip-sync | Mouth mismatch, visual artifacts, wrong face |
| Audio | Clipping, dialogue/M&E imbalance, noise, loudness |
| Subtitle | Reading speed, overflow, timing, spelling |

### 34.2 Dub score

Compute a transparent weighted score from measurable checks; do not present it as “truth”. The editor sees both score and underlying issues. A project can define release gates, for example: no critical issues, translation score above threshold, all principal-character lines approved.

## 35. Security, Privacy and Rights

### 35.1 Local-first security

• Project media stays local by default.

• Cloud/provider use is per-project and visibly indicated.

• Provider keys are stored encrypted, never plaintext in logs.

• Sensitive logs can be disabled or redacted.

• Project files use hashes to detect accidental corruption.

• Private Studio mode blocks all external AI provider calls.

### 35.2 Voice and content rights

• Require authorization status before enabling cloning of a named/reference voice.

• Store consent/rights evidence metadata without embedding sensitive documents into prompts.

• Support immediate voice-profile disable/revocation.

• Maintain audit trail for voice assignment and export.

• Warn that users are responsible for rights to source media and distribution.

## 36. Reliability, Errors and Recovery

| Failure | Expected behavior |
| --- | --- |
| Provider timeout | Retry bounded times → fallback provider → mark degraded if all fail |
| Malformed LLM JSON | Schema repair prompt → fallback → manual review |
| FFmpeg error | Preserve logs, identify stream/codec, offer transcode-safe path |
| GPU OOM | Unload models → retry lower batch/precision → queue/fallback |
| Model crash | Worker restarts; UI/project remains open |
| Power/app crash | Resume completed jobs from checkpoints |
| Missing source file | Project opens read-only/degraded; prompt to relink media |
| Disk full | Pause render before corruption; show required free space |
| Lip-sync artifact | Reject generated shot; use original video with dubbed audio |

## 37. Testing and Validation Strategy

### 37.1 Automated tests

• Unit tests for timing math, schemas, provider routing, cache keys and project migrations.

• Integration tests using short licensed/public-domain clips for complete pipeline paths.

• FFmpeg golden tests comparing stream metadata and expected outputs.

• Provider contract tests with mocked and real health-check responses.

• GUI tests for critical project/edit/render flows using pytest-qt.

• Crash-recovery tests that terminate workers mid-job and verify resume.

• Performance benchmarks by clip duration, GPU model and quality preset.

### 37.2 Quality benchmark set

Maintain a small internal evaluation suite spanning clean dialogue, overlap, music-heavy scenes, multiple speakers, whisper/shout, close-up lip-sync, off-screen speech, accents and several target languages. Score ASR, translation, timing, voice similarity, intelligibility and visual artifacts.

## 38. Windows Packaging and Distribution

### 38.1 User experience

The user installs one Windows application and never needs to install Python manually. Bundle the Python runtime, Qt libraries, required helper executables and application code using a standalone packaging strategy. Large AI models are better managed as optional downloadable packages rather than embedding everything in the installer.

### 38.2 First-run setup

1. Detect Windows version, CPU, RAM, GPU, VRAM and disk.

2. Test FFmpeg runtime.

3. Test CUDA/PyTorch compatibility if NVIDIA GPU exists.

4. Select recommended quality mode.

5. Ask model storage/cache/project locations.

6. Install or register baseline models.

7. Run a short self-test.

### 38.3 Update channels

Separate application updates from model-package updates. The user can pin a model version for reproducibility and roll back application versions if a project depends on older behavior.

## 39. Settings and Configuration

| Category | Key settings |
| --- | --- |
| General | Autosave, recent projects, startup behavior, language |
| Appearance | Theme, scaling, panel layout, waveform density |
| Performance | Worker count, performance mode, cache size |
| GPU | Preferred devices, VRAM reserve, model residency |
| AI Models | Model paths, precision, default engines |
| Providers | Endpoints, credentials, order, timeout, failover |
| Translation | Default provider, context window, glossary policy |
| Voice | Engine, sample rate, cloning restrictions, default quality |
| Lip-sync | Preview/final engine, visibility threshold |
| Audio | Working sample rate, loudness target, mix defaults |
| Storage | Project, cache, model, temp, render folders |
| Privacy | Private mode, logs, provider uploads |
| Shortcuts | Custom timeline/editor actions |
| Advanced | Diagnostics, experimental engines, developer mode |

## 40. Internal Service Contracts

### 40.1 Event model

| job.started<br>job.progress<br>job.checkpoint<br>job.completed<br>job.failed<br>artifact.created<br>project.changed<br>provider.health_changed<br>model.loaded<br>model.unloaded<br>qc.issue_created |
| --- |

### 40.2 Representative Python service interfaces

```text
class TranslationService:<br>    async def translate_scene(self, scene_id, target_lang, policy) -> TranslationBatch: ...<br><br>class VoiceService:<br>    async def synthesize(self, utterance_id, voice_profile_id, controls) -> VoiceArtifact: ...<br><br>class RenderService:<br>    async def render_localization(self, project_id, language, preset) -> RenderJob: ...
```

## 41. Quality Presets

| Preset | Pipeline behavior |
| --- | --- |
| Instant Preview | Fast ASR/translation/voice; no final lip-sync; proxy media |
| Fast | Good local ASR, standard voice, timing correction, limited QC |
| Professional | Full speaker/character workflow, premium voice, selective lip-sync, mixing, QC |
| Cinema | Highest configured models, multi-pass translation/QC, final lip-sync, acoustic matching, master |
| Offline Private | Best local-only engines allowed by hardware; no provider calls |

## 42. Development Roadmap

| Phase | Deliverables |
| --- | --- |
| Phase 0 — Foundation | PySide6 shell, project model, settings, DB, logging, FFmpeg probing, worker framework. |
| Phase 1 — Audio Dub MVP | ASR, diarization, translation router, voice generation, timing, stereo mix, SRT, export. |
| Phase 2 — Professional Editor | Timeline, character studio, translation editor, versions, autosave/recovery, QC basics. |
| Phase 3 — Audio Intelligence | Stem separation, pronunciation tools, acoustic matching, improved mixer. |
| Phase 4 — Visual Intelligence | Shot/face analysis, active speaker association, lip-sync preview/final engines. |
| Phase 5 — Multilingual Scale | Shared source analysis, multi-language dashboards, batch render queue. |
| Phase 6 — Reliability & Packaging | Installer, model manager, diagnostics, updates, crash recovery hardening. |
| Phase 7 — Studio Edition | Advanced audio channels, team/project archive tools, automation API/CLI, enterprise privacy. |

## 43. Suggested Milestones and Acceptance Criteria

### Milestone A — Project can open and analyze media

• Create/reopen project

• Probe streams

• Generate proxy/waveform

• Run jobs without freezing UI

• Resume after restart

### Milestone B — End-to-end audio dubbing works

• ASR + speaker labels

• Translate through provider router

• Generate distinct character voices

• Match timing within configured tolerance

• Mix with original M&E/stems

• Export playable dubbed file

### Milestone C — Professional editing

• Edit any line

• Regenerate one line only

• Version comparison

• Character reassignment

• Glossary and pronunciation

• QC issue workflow

• Undo/redo and autosave

### Milestone D — Visual dubbing

• Face/shot analysis

• Active speaker confidence

• Selective lip-sync

• Fallback to original shot

• Final render without unnecessary full-video regeneration

## 44. Recommended V1 / MVP

| DO NOT START WITH LIP-SYNC  The most valuable first release is a reliable professional audio dubbing workstation. Lip-sync should be added only after transcript, character voices, timing, mixing, editing and recovery are solid. |
| --- |

### 44.1 MVP must include

• Windows PySide6 app

• Project/media import

• FFprobe/FFmpeg layer

• ASR + timestamps

• Speaker diarization

• Character assignment

• DeepSeek/Gemini/ChatGPT provider router

• Context-aware translation

• Glossary

• Local voice engine abstraction

• Voice assignment per character

• Timing alignment

• Music/effects preservation or basic stem separation

• Subtitle generation

• Line-level editor

• Render queue

• Crash recovery

• MP4/MKV export

• Model/provider settings

### 44.2 MVP can postpone

• High-quality lip-sync

• Complex 5.1/7.1 mastering

• Full face-character identity across seasons

• Advanced acoustic reconstruction

• Cloud cluster rendering

• Team collaboration/server edition

## 45. Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Unofficial API breaks | Translation/QC unavailable | Adapters, health checks, fallback chain, local LLM option |
| Model licensing changes | Commercial release blocked | Maintain model registry and release-time license audit |
| Voice rights misuse | Legal/ethical exposure | Consent records, disable unauthorized cloning, audit |
| GPU variability | Poor performance/OOM | Hardware profiles, model tiers, VRAM scheduler, CPU fallback |
| Lip-sync artifacts | Visible quality loss | Selective shots, QC, original-shot fallback |
| Source separation damage | Music/SFX artifacts | Prefer M&E, quality thresholds, manual stem override |
| Long project crashes | Lost work | Checkpoint DAG, immutable artifacts, autosave, recovery |
| LLM translation inconsistency | Terminology drift | Glossary, character bible, translation memory, QC pass |
| Installer size | Bad UX | Small core installer + model packages |
| Disk consumption | Hundreds of GB | Cache quotas, deduplication, cleanup UI, estimates before render |

## 46. Provider Secrets and Local Credential Design

Provider credentials must never be embedded in project files. Store them in a Windows-protected credential store or encrypt them with a machine/user-bound secret. The database should keep only provider IDs and non-sensitive configuration.

### 46.1 API request policy

• Redact source file paths and unrelated metadata from prompts.

• Send only the minimum text/context required for the requested operation.

• Per-project switch: local only / allow text cloud / allow media cloud.

• Implement global and per-provider rate limits.

• Record request IDs, latency, status and token/usage estimates where available.

• Allow user to purge provider history/cache.

## 47. Artifact, Version and Reproducibility Model

Every AI output is an artifact with provenance: source artifact hashes, engine ID/version, model ID/version, provider/prompt version, parameters, timestamp and quality metrics. This allows a line or final render to be reconstructed or compared later.

| Translation v3<br>  source_utterance_hash<br>  provider=gemini_adapter<br>  prompt_version=translate_scene_1.4<br>  glossary_version=7<br><br>Voice v5<br>  translation_version=3<br>  voice_profile=TONY_BN_v2<br>  model=f5_local_profile_A<br>  seed=...<br>  target_duration=2.82s |
| --- |

## 48. Logging, Diagnostics and Observability

• Structured application log

• Per-job log

• FFmpeg stderr capture

• GPU/VRAM sample history

• Provider health and latency dashboard

• Model load/unload events

• Crash dump metadata

• User-exportable diagnostics bundle with secrets removed

Never write API secrets or full sensitive provider payloads to standard logs. Developer mode can capture additional data only with explicit consent.

## 49. Optional Local CLI / Automation Interface

Although the primary product is graphical, a Python CLI makes testing, batch production and future integration much easier.

| aidub new --source movie.mkv --project MovieProject<br>aidub analyze MovieProject<br>aidub translate MovieProject --lang bn-BD<br>aidub dub MovieProject --lang bn-BD --preset professional<br>aidub qc MovieProject --lang bn-BD<br>aidub render MovieProject --lang bn-BD --output movie_bn.mkv |
| --- |

The CLI calls the same services as the GUI; there should not be a second implementation of business logic.

## 50. Example User Workflow — English Movie to Bengali

1. User drops movie.mkv into the New Project wizard.

2. App probes video/audio/subtitles, estimates disk/model requirements and creates proxy.

3. Analysis jobs extract audio, separate stems, detect scenes, transcribe and diarize speakers.

4. Editor names principal speakers and assigns/creates authorized Bengali voice profiles.

5. Translation engine builds scene context and asks the LLM router for Bengali dialogue using glossary and duration limits.

6. QC flags uncertain terms and long lines; editor approves or edits them.

7. Voice workers generate Bengali performances with emotion/timing targets.

8. Timing engine adjusts translations/voice outputs and only time-stretches small residual differences.

9. Audio mixer places dialogue over M&E and applies acoustic scene presets.

10. Optional lip-sync is generated for high-visibility close-up shots.

11. QC heatmap highlights remaining issues; editor regenerates selected lines/shots.

12. Render job produces MKV/MP4 with original and Bengali audio tracks plus Bengali subtitles.

## 51. Engineering Principles

• Local-first by default; cloud is an augmentation layer.

• No long task on the UI thread.

• Immutable artifacts, mutable edit decisions.

• Schema-validated AI outputs only.

• Provider/model independence everywhere.

• Never recompute what can be cached safely.

• Never re-render the full film to fix one line.

• Audio dubbing must work even when visual AI fails.

• Quality scores must be explainable by underlying checks.

• User rights, privacy and voice authorization are part of architecture.

• Every automated action must have a manual override in professional mode.

## 52. Future Expansion

• Remote GPU worker over LAN/VPN

• Studio team collaboration

• Project server and shared asset store

• Human translator/actor assignment workflow

• ADR recording inside the application

• Professional 5.1/7.1 mixer

• Audio-description generation

• Live dubbing mode

• Streaming localization API

• Model marketplace/package registry

• Character continuity across seasons/franchises

• Automatic dubbing director that ranks multiple performances

• Hardware-specific TensorRT/ONNX model builds

• Plugin SDK for third-party engines

## 53. Final Architecture Decisions

| Decision | Chosen direction |
| --- | --- |
| Windows framework | PySide6 / Qt Widgets driven entirely from Python |
| Application language | Python 3.x |
| Media layer | FFmpeg/FFprobe controlled by Python |
| Local DB | SQLite + SQLAlchemy/SQLModel |
| Concurrency | asyncio for orchestration; worker processes/subprocesses for heavy tasks |
| AI philosophy | Dedicated local media models + LLM reasoning/router |
| LLM providers | DeepSeek, Gemini and ChatGPT-style unofficial adapters; pluggable/fallback by design |
| ASR | Local GPU speech engine with word timestamps |
| Voice | Pluggable local multilingual voice engine with authorization layer |
| Lip-sync | Separate preview/final engines; selective-shot processing |
| Rendering | Non-destructive artifact graph + FFmpeg |
| Distribution | Standalone Windows app; models installed separately/optionally |
| Privacy | Local-first with strict Private Studio mode |
| MVP order | Audio dubbing/editor first; advanced lip-sync second |

## 54. Production Readiness Checklist

☐ Core project/database migrations tested

☐ App opens projects after abnormal shutdown

☐ All provider credentials encrypted

☐ Provider fallback works

☐ Offline/private mode passes network-deny test

☐ Model licenses audited

☐ Voice authorization workflow implemented

☐ ASR accuracy benchmarked on target languages

☐ Translation glossary consistency benchmarked

☐ Line-level regeneration does not invalidate unrelated artifacts

☐ GPU OOM recovery tested

☐ Disk-full behavior tested

☐ FFmpeg failure diagnostics readable

☐ Export files validated in multiple players

☐ Subtitles validated

☐ QC release gates configurable

☐ Installer tested on clean Windows machine

☐ Uninstall preserves or explicitly offers to preserve projects

☐ Secrets/log redaction audit complete

☐ Dependency/model version inventory included in About screen

## 55. Glossary

| Term | Meaning |
| --- | --- |
| ASR | Automatic Speech Recognition. |
| VAD | Voice Activity Detection; detects regions containing speech. |
| Diarization | Determines “who spoke when”. |
| M&E | Music & Effects track used to rebuild foreign-language mixes. |
| Prosody | Rhythm, pitch, stress and phrasing of speech. |
| TTS | Text-to-Speech. |
| Voice cloning | Generating speech conditioned on an authorized reference voice. |
| Lip-sync | Aligning visible mouth movement to target speech. |
| Artifact | Versioned generated file or metadata output from a pipeline stage. |
| DAG | Directed Acyclic Graph describing job dependencies. |
| Proxy | Lower-resolution/bitrate media for fast editing preview. |
| Remux | Change container/tracks without re-encoding video. |
| Translation memory | Stored approved translations reused for consistency. |
| Character bible | Project context describing characters, terminology, style and relationships. |
| Private Studio mode | Local-only processing mode that blocks external provider calls. |

## 56. Conclusion

The recommended product is not a single AI feature but a complete Windows post-production system. Python can own the full application layer—PySide6 UI, project engine, database, orchestration, workers, provider adapters, FFmpeg control, model loading, editing and packaging—while optimized native runtimes handle the computational work they are designed for.

The safest and most scalable strategy for your unofficial DeepSeek, Gemini and ChatGPT access is to use them behind a strict provider router for translation, dialogue adaptation, context reasoning and QC. The professional dubbing core must remain independent through local ASR, diarization, voice, audio and lip-sync engines so that provider outages or account changes cannot break the product.

| RECOMMENDED BUILD ORDER  Foundation → audio dubbing MVP → professional editor → audio intelligence → visual/lip-sync → multi-language scale → packaging and studio hardening. |
| --- |

## 57. Enterprise Architecture Upgrade

> Design principle  The application is a Windows desktop post-production workstation. Python remains the implementation language, while heavy inference runs in isolated worker processes so the GUI never freezes and GPU failures do not terminate the editor.

### 57.1 Runtime process topology

```text
AIDubbingStudio.exe / pythonw.exe<br>│<br>├── UI Process (PySide6)<br>│   ├── Project Workspace<br>│   ├── Timeline / Editors<br>│   ├── Job Monitor<br>│   └── IPC Client<br>│<br>├── Orchestrator Process<br>│   ├── DAG Scheduler<br>│   ├── Checkpoint Manager<br>│   ├── Cache Index<br>│   └── Provider Router<br>│<br>├── Media Worker Pool<br>│   ├── FFmpeg / FFprobe<br>│   ├── Proxy / Waveform / Thumbnail<br>│   └── Mux / Encode / Mix<br>│<br>├── CPU AI Worker Pool<br>│   ├── Text normalization<br>│   ├── LLM calls / validation<br>│   ├── Subtitle processing<br>│   └── QC aggregation<br>│<br>└── GPU Worker Pool<br>    ├── ASR<br>    ├── Diarization / embeddings<br>    ├── TTS / voice conversion<br>    ├── Separation<br>    └── Lip-sync / vision
```

### 57.2 Why process isolation is mandatory

- Python GUI threads must not execute long PyTorch/CUDA inference directly; use multiprocessing or dedicated worker executables.
- A CUDA out-of-memory error must fail only the current task, not the project or UI.
- Models can remain warm inside workers, eliminating repeated load/unload latency.
- Per-engine workers can be restarted independently after crashes or driver faults.
- Windows packaging can ship the UI and workers as one product while keeping their failure domains separate.
## 58. Numbered Product Requirements

### 58.1 Functional requirements

| ID | Area | Requirement | Priority |
| --- | --- | --- | --- |
| FR-001 | Project lifecycle | Create, open, duplicate, archive, relink and recover projects without modifying the original source media. | P0 |
| FR-002 | Media ingestion | Import MP4/MKV/MOV and inspect streams, chapters, subtitles, frame rate, codecs, HDR flags and channel layout with FFprobe. | P0 |
| FR-003 | Proxy workflow | Generate edit proxies, waveform caches and thumbnails while final render references original media. | P0 |
| FR-004 | ASR | Produce segment-, utterance- and word-level timestamps with language and confidence metadata. | P0 |
| FR-005 | Diarization | Assign stable speaker IDs and support manual split/merge/relabel corrections. | P0 |
| FR-006 | Character memory | Map speakers/faces to persistent characters and retain voice, pronunciation, style and relationship metadata. | P0 |
| FR-007 | Translation | Generate context-aware, duration-aware, glossary-aware translations with multiple alternatives and version history. | P0 |
| FR-008 | Provider routing | Route reasoning tasks across DeepSeek, Gemini and ChatGPT-style adapters with schema validation, retries and fallback. | P0 |
| FR-009 | Voice generation | Generate or convert authorized character voices using swappable local/cloud engines. | P0 |
| FR-010 | Performance control | Expose emotion, pace, pitch, energy, pause and emphasis controls at utterance level. | P1 |
| FR-011 | Timing | Fit dubbed speech to the source slot using rewrite, pause optimization and bounded time-stretch. | P0 |
| FR-012 | Stem handling | Prefer supplied M&E; otherwise separate dialogue/music/effects and retain source stems as immutable artifacts. | P0 |
| FR-013 | Lip-sync | Apply visual lip correction only to eligible high-visibility speaking shots and support preview/final engines. | P1 |
| FR-014 | Timeline editor | Provide multi-track video/audio/subtitle editing, markers, snapping, zoom, solo/mute/lock and non-destructive versions. | P0 |
| FR-015 | QC | Score and flag translation, voice, timing, pronunciation, speaker identity, clipping, loudness and lip alignment. | P0 |
| FR-016 | Render queue | Render multiple languages/projects with pause/resume, crash recovery and partial rerender. | P0 |
| FR-017 | Offline mode | Allow a project policy that disables all network providers and keeps processing local. | P1 |
| FR-018 | Model manager | Install, verify, benchmark, load, unload and remove local models with disk/VRAM estimates. | P1 |
| FR-019 | Rights ledger | Track content rights, voice consent/license scope, expiry and audit history. | P0 |
| FR-020 | Diagnostics | Generate a support bundle containing sanitized logs, environment versions and job traces without leaking API secrets. | P1 |

### 58.2 Non-functional requirements

| ID | Quality Attribute | Requirement |
| --- | --- | --- |
| NFR-001 | Responsiveness | UI interactions should remain responsive during any analysis or render operation; long work never runs on the UI thread. |
| NFR-002 | Recoverability | Completed stages are checkpointed; restarting the app resumes from the last valid artifact rather than reprocessing the film. |
| NFR-003 | Determinism | Every generated artifact records engine, model, version, seed/settings, prompt version, input hash and dependency hashes. |
| NFR-004 | Privacy | Secrets are stored encrypted; logs are redacted; offline projects must not make network calls. |
| NFR-005 | Scalability | The same project model must support a single laptop GPU and multiple local/remote workers without changing editor semantics. |
| NFR-006 | Observability | Every job emits structured events, duration, throughput, GPU memory, warnings and failure reason. |
| NFR-007 | Quality safety | Low-confidence AI output is surfaced for review instead of silently accepted. |
| NFR-008 | Accessibility | Keyboard operation, readable focus states, scalable text and high-contrast modes are supported. |
| NFR-009 | Compatibility | Windows 10/11 x64 is the primary deployment target; GPU acceleration is optimized for supported NVIDIA CUDA configurations. |
| NFR-010 | Maintainability | Engine-specific code is isolated behind typed interfaces and contract tests. |

## 59. AI Provider Router - Production Contract

> Important  Unofficial DeepSeek, Gemini or ChatGPT endpoints must be treated as optional and unstable integrations. Use them only when you are authorized to do so. Never let provider-specific request formats leak into translation, QC or orchestration code.

### 59.1 Logical provider interface

```text
class LLMProvider(Protocol):<br>    provider_id: str<br><br>    async def health_check(self) -> HealthStatus: ...<br>    async def generate(self, request: LLMRequest) -> LLMResponse: ...<br>    async def estimate_cost(self, request: LLMRequest) -> CostEstimate: ...<br>    async def capabilities(self) -> ProviderCapabilities: ...
```

### 59.2 Canonical request

```text
{<br>  "task": "duration_aware_translation",<br>  "project_id": "prj_...",<br>  "utterance_id": "utt_...",<br>  "source_language": "en",<br>  "target_language": "bn",<br>  "source_text": "What are you doing here?",<br>  "context": {<br>    "previous_lines": [],<br>    "next_lines": [],<br>    "character": {},<br>    "scene": {},<br>    "glossary": {}<br>  },<br>  "constraints": {<br>    "target_duration_ms": 2480,<br>    "max_duration_error_pct": 8,<br>    "preserve_names": true,<br>    "rating": "PG-13"<br>  },<br>  "response_schema": "translation.v2"<br>}
```

### 59.3 Canonical response validation

- Reject responses that do not satisfy the expected JSON schema.
- Validate language, empty fields, forbidden content transformations, glossary terms and duration estimate.
- Store provider ID, latency, retry count and response hash with the translation version.
- Never accept markdown-wrapped or conversational text when the task contract requires JSON.
- Retry only idempotent operations; use bounded exponential backoff with jitter.
- Circuit-break a failing provider and route new tasks to a healthy fallback until its cool-down expires.
### 59.4 Recommended task routing

| Task | Routing Policy | Creativity | Output Constraint |
| --- | --- | --- | --- |
| Literal translation draft | Fastest healthy LLM | Low/medium | JSON translation schema |
| Cultural adaptation | Gemini/ChatGPT/DeepSeek adapter ranked by benchmark | Medium | Context + glossary + audience |
| Duration rewrite | Best measured model for target language | Medium | Strict duration budget |
| Translation critique | Different provider from generator when available | Low | Independent reviewer |
| QC explanation | Cheap/fast healthy provider | Low | Issue object only |
| Scene summary / memory | Fast healthy provider | Low | Structured scene memory |
| Fallback when all fail | Local model or manual review | None | Never block project opening/editing |

## 60. Local AI Model Registry and Benchmark Policy

### 60.1 Registry fields

| ModelRecord:<br>  model_id<br>  engine_type            # asr \| diarization \| tts \| separation \| lipsync \| vision<br>  display_name<br>  version<br>  source<br>  license<br>  model_hash<br>  supported_languages<br>  minimum_vram_mb<br>  recommended_vram_mb<br>  compute_precision<br>  benchmark_score<br>  benchmark_hardware<br>  last_verified_at<br>  install_path<br>  status                  # installed \| verified \| incompatible \| broken |
| --- |

### 60.2 Candidate engine strategy

| Subsystem | Candidate Direction | Product Policy |
| --- | --- | --- |
| ASR | faster-whisper/CTranslate2-class local ASR | Fast local transcription, quantized inference options, word/segment timing support. |
| Diarization | pyannote.audio-class pipeline | Speaker segmentation, embeddings and clustering; manual correction remains first-class. |
| Source separation | Demucs-class separation | Useful when no clean M&E track exists; never assume separation artifacts are studio-equivalent. |
| TTS/voice | Pluggable local multilingual engines such as Chatterbox/Fish Speech/F5-TTS-class candidates | Benchmark by target language, speaker similarity, stability and rights/license suitability before enabling by default. |
| Fast lip-sync | MuseTalk-class engine | Preview/interactive path for eligible shots. |
| High-quality lip-sync | LatentSync-class engine | Final render path where quality justifies higher compute cost. |

> Benchmark before defaulting  No model should become the application default solely because it is popular. Maintain a controlled benchmark suite for English, Bengali, Hindi and other target languages, and record quality + speed per GPU tier.

## 61. Windows Concurrency, IPC and State Model

### 61.1 Concurrency rules

- PySide6 UI communicates with workers through a typed IPC layer; do not share mutable editor state directly with workers.
- Use QThread only for lightweight UI-side I/O and adapters. Use multiprocessing for CPU-heavy or GPU-heavy inference.
- One GPU worker owns a model instance and its CUDA context whenever practical.
- Cancel requests cooperatively at safe checkpoints; never corrupt already-completed immutable artifacts.
- Persist job state before emitting a terminal success event.
- The editor reads from the project database and artifact index, not from worker-local memory.
### 61.2 Event envelope

```text
{<br>  "event_id": "evt_...",<br>  "timestamp": "2026-08-14T01:55:00+06:00",<br>  "project_id": "prj_...",<br>  "job_id": "job_...",<br>  "stage": "tts",<br>  "type": "progress",<br>  "progress": 0.72,<br>  "message": "Generated 183 / 254 utterances",<br>  "metrics": {<br>    "gpu_id": 0,<br>    "vram_used_mb": 9412,<br>    "rtf": 0.31<br>  }<br>}
```

## 62. Data Architecture and Core Schemas

### 62.1 Core entity relationship

```text
Project<br>├── MediaAsset<br>│   ├── VideoTrack<br>│   ├── AudioTrack<br>│   └── SubtitleTrack<br>├── Scene<br>│   └── Shot<br>│       └── FaceTrack<br>├── Character<br>│   ├── SpeakerIdentity<br>│   ├── VoiceProfile<br>│   └── ConsentRecord<br>├── Utterance<br>│   ├── TranscriptVersion<br>│   ├── TranslationVersion[]<br>│   ├── VoiceTake[]<br>│   ├── TimingVersion[]<br>│   └── QCResult[]<br>├── LanguageVariant[]<br>├── Artifact[]<br>└── Job[]
```

### 62.2 Utterance record

```text
{<br>  "id": "utt_000183",<br>  "scene_id": "scn_012",<br>  "speaker_id": "spk_003",<br>  "character_id": "char_tony",<br>  "start_ms": 418230,<br>  "end_ms": 420710,<br>  "source_text": "What are you doing here?",<br>  "language": "en",<br>  "confidence": 0.97,<br>  "emotion": {"label": "surprise", "intensity": 0.74},<br>  "prosody": {"rate": 1.04, "energy": 0.79},<br>  "visibility": {"active_face": "face_7", "priority": "high"},<br>  "locked_fields": []<br>}
```

### 62.3 Artifact provenance

| Artifact:<br>  artifact_id<br>  artifact_type<br>  path<br>  sha256<br>  source_artifact_ids[]<br>  engine_id<br>  model_id<br>  model_version<br>  parameters_json<br>  prompt_version<br>  created_at<br>  created_by<br>  reproducibility_level |
| --- |

## 63. Cache, Invalidation and Partial Re-rendering

### 63.1 Cache key

| cache_key = SHA256(<br>    engine_id + model_version +<br>    normalized_inputs_hash +<br>    settings_hash +<br>    prompt_version +<br>    dependency_artifact_hashes<br>) |
| --- |

### 63.2 Dependency-aware invalidation

| User Change | Required Invalidation |
| --- | --- |
| Change translation text | Invalidate selected language TTS -> timing -> optional lip-sync -> mix -> export; keep ASR, stems, scene analysis. |
| Change voice profile | Invalidate character TTS takes -> dependent timing/lip-sync/mixes; keep translations. |
| Change source media | Invalidate every analysis artifact dependent on the changed source fingerprint. |
| Change glossary | Mark affected translations stale; do not automatically destroy approved human edits. |
| Change lip-sync engine | Invalidate only visual lip artifacts and renders that depend on them. |
| Change music level | Invalidate mix/master/export only. |

## 64. GPU/VRAM Scheduler Specification

### 64.1 Hardware tiers

| Hardware Tier | Mode | Scheduling Policy |
| --- | --- | --- |
| CPU-only / iGPU | Fallback | ASR small/medium, text work, basic editing; heavy TTS/lip-sync may require cloud/remote worker. |
| 6-8 GB VRAM | Entry | Load one heavy model at a time; aggressive unload and FP16/INT8 where validated. |
| 10-16 GB VRAM | Recommended | Keep one or two core models warm; professional audio dubbing practical. |
| 20-24+ GB VRAM | High-end | Parallel or resident models, high-quality lip-sync, larger batch sizes. |
| Multi-GPU | Studio | Pin workers/models by GPU; schedule independent scenes/languages concurrently. |

### 64.2 OOM recovery

1. Catch the worker failure and record exact requested/free VRAM.
1. Reduce batch size or chunk size and retry once.
1. If still failing, unload nonessential resident models and retry.
1. If still failing, downgrade precision/model according to project policy or queue to another GPU.
1. Never silently downgrade quality in Cinema mode; require a visible warning/decision.
## 65. Professional UI/UX Specification

### 65.1 Visual system

| Design Area | Specification |
| --- | --- |
| Application shell | Charcoal/navy surfaces, restrained indigo/cyan accent, high contrast, no consumer-style oversized cards. |
| Typography | Aptos/Segoe-style UI typography; monospaced font only for logs, paths, JSON and timecode. |
| Density | Professional compact density with optional Comfortable mode. |
| Status colors | Green=healthy/approved; amber=review; red=blocking; blue=processing/information. |
| Motion | Short functional transitions only; disable/reduce with accessibility setting. |
| Icons | Consistent vector icon set; avoid emoji in production controls. |
| Timecode | Always display HH:MM:SS.mmm or project frame timecode consistently. |

### 65.2 Main editor layout

```text
┌────────────────────────────────────────────────────────────────────┐<br>│ Menu  Project  Edit  AI  Voice  Subtitle  Render      GPU / Jobs │<br>├──────────────┬─────────────────────────────────────┬───────────────┤<br>│ Project Bin  │              Viewer                 │ Inspector     │<br>│ Scenes       │      Source / Dub / Compare         │ Character     │<br>│ Characters   │                                     │ Translation   │<br>│ Languages    │                                     │ Voice / QC    │<br>├──────────────┴─────────────────────────────────────┴───────────────┤<br>│ Timeline: V1 Original \| V2 Lip \| A1 M&E \| A2 Dub \| S1 Subtitle   │<br>│                                                                    │<br>├────────────────────────────────────────────────────────────────────┤<br>│ Status: Autosaved \| Job progress \| Cache \| GPU \| Warnings         │<br>└────────────────────────────────────────────────────────────────────┘
```

### 65.3 Command palette and shortcuts

| Shortcut | Action |
| --- | --- |
| Ctrl+K | Open command palette |
| Space | Play / pause |
| J / K / L | Reverse / stop / forward shuttle |
| Ctrl+S | Manual save snapshot |
| Ctrl+Z / Ctrl+Y | Undo / redo |
| Ctrl+R | Regenerate selected voice take |
| Alt+T | Re-translate selected utterance |
| Alt+L | Run lip-sync on selected shot |
| Ctrl+Shift+E | Open export panel |
| F | Fullscreen viewer |
| M | Add marker |
| S | Split selected clip/utterance at playhead |
| + / - | Timeline zoom |

## 66. Complete Professional Screen Map

| # | Screen | Purpose |
| --- | --- | --- |
| 01 | Launch / Recovery | Recent projects, crash recovery, safe mode, update status. |
| 02 | Home Dashboard | Projects, render queue, GPU summary, storage, recent errors. |
| 03 | New Project Wizard | Source media, languages, preset, privacy policy, cache/storage location. |
| 04 | Media Import | Stream inspection, track selection, proxy plan, M&E selection. |
| 05 | Project Workspace | Master navigation across scenes, characters, languages and assets. |
| 06 | Analysis Center | ASR, diarization, separation, scene analysis progress and confidence. |
| 07 | Scene Browser | Scene/shot grid, metadata, quality heatmap and batch actions. |
| 08 | Character Studio | Character identity, face tracks, speaker mapping, role notes and voice lock. |
| 09 | Voice Studio | Voice library, authorized reference clips, test phrases, similarity and style controls. |
| 10 | Translation Studio | Source/target grid, alternatives, context, glossary, approvals, batch QA. |
| 11 | Pronunciation Studio | Dictionary, phoneme overrides, names, acronyms, preview. |
| 12 | Performance Studio | Emotion, pace, energy, pitch, pause, emphasis and take versions. |
| 13 | Timeline Editor | Multi-track professional editing and utterance alignment. |
| 14 | Lip-Sync Studio | Eligibility, face tracks, preview/final engines, before/after compare. |
| 15 | Audio Mixer | Dialogue/M&E/stems, EQ, dynamics, reverb matching, loudness, channel routing. |
| 16 | Subtitle Studio | SRT/VTT/ASS, line breaks, reading speed, styles, SDH support. |
| 17 | Quality Control | Dub score, issue list, heatmap, auto-fix candidates, approval status. |
| 18 | Render Queue | Queued/running/paused/failed jobs, GPU assignment, ETA/throughput. |
| 19 | Export Center | Container, codecs, language tracks, subtitles, naming, archive package. |
| 20 | AI Provider Manager | DeepSeek/Gemini/ChatGPT adapter endpoints, health, limits, fallback order. |
| 21 | Model Manager | Installed local models, hashes, licenses, disk/VRAM estimates, benchmarks. |
| 22 | GPU & Performance | Devices, VRAM, worker assignment, precision, thermal/power policy. |
| 23 | Storage & Cache | Locations, project sizes, cleanup, relink, cache validation. |
| 24 | Privacy & Rights | Offline policy, consent records, content rights, audit log. |
| 25 | Diagnostics | Structured logs, failed jobs, dependency versions, support-bundle export. |
| 26 | Settings | General, appearance, shortcuts, audio, rendering, providers, advanced. |

## 67. Professional Audio and Mastering Contract

### 67.1 Signal path

```text
Dub Voice Take<br>  -> de-click / de-noise if needed<br>  -> corrective EQ<br>  -> dynamics / de-essing<br>  -> scene acoustic matching<br>  -> distance / spatial placement<br>  -> dialogue bus<br><br>M&E / Music / FX / Ambience<br>  -> preservation / cleanup<br>  -> automation / ducking only when needed<br>  -> master bus<br><br>Master Bus<br>  -> channel-layout validation<br>  -> true-peak protection<br>  -> loudness target preset<br>  -> export stem / final mix
```

### 67.2 Audio rules

- Never destructively overwrite M&E or extracted source stems.
- Do not normalize each utterance independently in a way that destroys scene dynamics.
- Store loudness targets as export presets because broadcast/streaming requirements differ.
- Any AI-generated room/acoustic treatment must be bypassable and A/B comparable.
- Preserve sample rate/channel metadata and document every channel remap.
## 68. Quality Metrics and Benchmark Gates

| Subsystem | Metric | Release Gate |
| --- | --- | --- |
| ASR | WER/CER by language; timestamp alignment error; named-entity accuracy | Dataset-specific; compare releases against fixed benchmark. |
| Diarization | DER/JER; speaker confusion; overlap handling | No regression beyond configured tolerance. |
| Translation | Human adequacy/fluency score; glossary accuracy; duration fit | Critical terminology 100% or requires review. |
| Voice | Speaker similarity; MOS-style human rating; pronunciation error rate | Per-language acceptance threshold. |
| Timing | Absolute duration error; overlap/gap violations | Professional preset targets tight slot fit. |
| Lip-sync | Audio-visual sync score + human close-up review | Blocking failures on high-priority shots. |
| Audio | Clipping, true peak, loudness, artifact/noise review | Export preset compliance. |
| Performance | Realtime factor by engine; VRAM peak; render throughput | Track by hardware tier. |
| Reliability | Job failure rate; resume success; corrupted artifact count | No data-loss failures in release candidate. |

> Golden benchmark  Create a legally usable internal benchmark pack with dialogue overlap, whispers, shouting, music-heavy scenes, multiple speakers, close-ups, off-screen speech, Bengali/Hindi names, code-switching and difficult acoustics. Run it before every model/provider upgrade.

## 69. Security, Provenance, Consent and Responsible Voice Use

### 69.1 Required controls

| Control | Requirement |
| --- | --- |
| Project rights | Record that the operator is authorized to process/localize the source media. |
| Voice rights | Store consent/license evidence, scope, languages, territory/use, expiry and revocation status for cloned or referenced voices. |
| Provider disclosure | Record which assets/text were sent to external providers for each job. |
| Secrets | Store credentials encrypted using Windows-protected storage or a dedicated encrypted local vault; never plaintext in project files. |
| Audit | Record creation, regeneration, export and rights-status changes with timestamps. |
| Watermark/provenance | Preserve or attach provenance metadata where supported and do not strip model-required watermarks. |
| Revocation | Block new renders using a revoked voice profile and surface affected historical assets. |

### 69.2 Network policy states

| Policy | Behavior |
| --- | --- |
| Offline | No external provider traffic; local models only. |
| Hybrid | Only explicitly enabled tasks may use external providers. |
| Cloud-assisted | External providers allowed but every request is logged and redacted according to policy. |
| Studio locked | Administrator/project policy prevents changes to provider or rights settings during production. |

## 70. Logging, Observability and Diagnostics

### 70.1 Structured log fields

```text
{<br>  "ts": "...",<br>  "level": "INFO",<br>  "component": "tts_worker",<br>  "project_id": "prj_...",<br>  "job_id": "job_...",<br>  "utterance_id": "utt_...",<br>  "engine": "voice_engine_x",<br>  "duration_ms": 2180,<br>  "gpu": 0,<br>  "vram_mb": 8120,<br>  "message": "generation completed"<br>}
```

### 70.2 Diagnostics bundle

- Application version, Python runtime and packaged dependency versions.
- Windows build, CPU/RAM/GPU/driver summary.
- Model registry entries and hashes, without redistributing model files.
- Sanitized recent job traces and crash reports.
- Provider health summary without API keys, cookies or authorization headers.
- Optional project manifest without media content.
## 71. Windows Packaging, Installation and Updating

### 71.1 Packaging strategy

- Package the GUI using PyInstaller or Nuitka after validating native-library compatibility; keep large models outside the core executable.
- Use pythonw/hidden worker executables so normal users never see console windows.
- Bundle a known FFmpeg/FFprobe build only after reviewing codec/license obligations for the intended distribution.
- Ship GPU prerequisites as checks/guidance rather than blindly overwriting user drivers.
- Sign production executables/installers with an appropriate Windows code-signing certificate.
- Support Stable, Beta and Development update channels with rollback metadata.
### 71.2 First-run wizard

1. Verify Windows version and writable storage locations.
1. Detect CPU, RAM, GPUs and available VRAM.
1. Verify FFmpeg runtime and media capabilities.
1. Offer recommended local model pack based on language and hardware.
1. Configure project/cache/model storage paths.
1. Configure privacy mode and optional providers.
1. Run a short hardware benchmark and save recommended preset.
## 72. Testing Architecture

### 72.1 Test pyramid

| Layer | Coverage |
| --- | --- |
| Unit | Pure functions: timestamps, duration math, cache keys, schema validation, path handling, text normalization. |
| Contract | Each ASR/TTS/LLM/lip-sync adapter must pass the same interface tests and failure-mode tests. |
| Integration | Real short media fixtures across FFmpeg -> ASR -> translate -> TTS -> mix. |
| GPU | OOM recovery, model reload, cancellation, batch size, deterministic settings where supported. |
| UI | Project open/save, timeline edits, keyboard commands, long-job responsiveness. |
| Regression | Golden benchmark outputs and quality metrics for each release. |
| Packaging | Clean Windows VM install, first run, model download, uninstall/repair/update. |

### 72.2 Must-test failure cases

- Provider returns HTML instead of JSON.
- Provider rate limit / timeout / invalid credential.
- GPU OOM halfway through a scene.
- Disk fills during render.
- Source media disappears or moves.
- App is terminated during database/artifact update.
- Malformed subtitle file.
- Corrupted cache artifact.
- Two speakers overlap.
- Off-screen dialogue incorrectly mapped to an on-screen face.
- User changes translation after lip-sync was already rendered.
## 73. Performance Presets and Service-Level Targets

| Preset | Pipeline | Intent |
| --- | --- | --- |
| Draft | Fast ASR, fast translation, fast/local voice, no lip-sync | Interactive review; prioritize throughput. |
| Fast | High-quality ASR + voice, limited QC, no/limited lip-sync | Creator-quality audio dub. |
| Professional | Full context translation, voice consistency, timing, stem mix, selective lip-sync, QC | Default serious production preset. |
| Cinema | Highest benchmarked models, strict QC, final lip-sync, human approval gates | Maximum quality; never silently downgrade. |

### 73.1 UI performance targets

- Project navigation and editor commands should feel immediate; heavy work is asynchronous.
- Waveform/thumbnails are cached and progressively loaded.
- Timeline scrolling/zooming must not trigger AI inference.
- Selecting an utterance should load text/metadata from local state, not wait for provider/network calls.
- Cancel/pause commands must be acknowledged promptly even if a worker finishes its current safe chunk before stopping.
## 74. Phased Implementation Plan

| Phase | Deliverables |
| --- | --- |
| Phase 0 - Foundation | Repo, PySide6 shell, project DB, settings, logging, FFmpeg wrapper, job/event infrastructure. |
| Phase 1 - Media + ASR | Import/probe/proxy/waveform, ASR, transcript editor, word timing, cache. |
| Phase 2 - Speakers + Translation | Diarization, character registry, DeepSeek/Gemini/ChatGPT adapters, glossary, translation studio. |
| Phase 3 - Voice + Timing | Voice engine abstraction, authorized references, takes, timing fitter, pronunciation editor. |
| Phase 4 - Audio Production | M&E/stems, separation fallback, dialogue processing, mixer, subtitles, audio-only export. |
| Phase 5 - Professional Editor | Timeline, non-destructive versions, markers, batch actions, QC heatmap. |
| Phase 6 - Visual Dubbing | Face tracking, active speaker, shot eligibility, MuseTalk/LatentSync-class adapters, compare UI. |
| Phase 7 - Reliability + Release | Crash recovery, installer, updater, signed build, diagnostics, benchmark gates. |
| Phase 8 - Studio Scale | Remote workers, multi-GPU scheduling, shared project storage, team/review workflow if needed. |

## 75. Definition of Done - Production Release

- A two-hour project can be opened, closed and resumed without re-running completed analysis.
- The UI remains responsive while ASR, TTS, separation, lip-sync and render jobs execute.
- A user can correct any speaker, transcript, translation, voice, timing or lip-sync decision manually.
- Changing one utterance does not force a full-film rerender.
- Every external LLM provider can be disabled without breaking project access or manual editing.
- Provider output is schema-validated and failures are visible, recoverable and logged.
- Local model versions and generated-artifact provenance are stored reproducibly.
- Voice cloning/reference cannot be activated without a rights/consent record in professional mode.
- Export validates streams, channels, subtitles, loudness/peak rules and missing assets before completion.
- Installer works on a clean supported Windows machine and the product runs without requiring a developer console.
- Golden benchmark has no blocking quality regressions.
- Crash and disk-full tests do not corrupt the project database or original media.
## 76. Copy-Paste Master Implementation Directive

> Use this section with an AI coding assistant  Paste the directive below together with the repository. It defines architectural boundaries and prevents the coding agent from simplifying the system into a single script or web application.

```text
PROJECT: AI Movie Dubbing Studio - Python-Only Windows Desktop Application<br><br>MISSION<br>Build a production-oriented Windows desktop application for professional multilingual movie dubbing. The product must be local-first, non-destructive, resumable, modular, GPU-aware, and capable of high-quality AI-assisted translation, voice generation, timing, audio mixing, subtitles, selective lip-sync and quality control.<br><br>NON-NEGOTIABLE ARCHITECTURE<br>1. Python is the implementation language.<br>2. PySide6/Qt is the desktop UI. Do not build the primary product as a browser dashboard.<br>3. Heavy AI/media work must run outside the UI thread in isolated worker processes.<br>4. FFmpeg/FFprobe handle media probing, decoding, encoding, remuxing and core audio/video operations.<br>5. The project is artifact/version based. Never overwrite original media.<br>6. Every long task is a cancellable/resumable job with progress, checkpoints and structured logs.<br>7. DeepSeek, Gemini and ChatGPT-style unofficial APIs are optional LLM providers behind adapters. Never couple business logic to a provider-specific payload. Use only endpoints the operator is authorized to use.<br>8. Validate every LLM response against a strict schema and provide retries, circuit breakers and fallback routing.<br>9. Dedicated local models handle ASR, diarization, source separation, TTS/voice, vision and lip-sync. LLM APIs are for language/reasoning/orchestration/QC, not the entire media pipeline.<br>10. Provide local/offline mode in which no network calls occur.<br>11. Cache by input/model/settings hashes and invalidate only downstream dependencies.<br>12. Support per-utterance manual overrides and A/B versions.<br>13. Treat voice rights/consent and source-content authorization as first-class project metadata.<br>14. Provide testable typed service interfaces and contract tests for every engine adapter.<br>15. Do not silently downgrade quality in Cinema mode.<br><br>CORE PIPELINE<br>Import -> Probe -> Proxy/Cache -> Scene/Shot Analysis -> Audio/Stems -> VAD/ASR -> Diarization -> Character/Face Mapping -> Translation/Adaptation -> Voice Generation -> Timing Fit -> Optional Lip-Sync -> Acoustic Matching/Mix -> Subtitles -> QC -> Render/Export.<br><br>UI<br>Provide Home, New Project, Media Import, Analysis Center, Scene Browser, Character Studio, Voice Studio, Translation Studio, Pronunciation Studio, Performance Studio, Timeline Editor, Lip-Sync Studio, Audio Mixer, Subtitle Studio, Quality Control, Render Queue, Export Center, Provider Manager, Model Manager, GPU/Performance, Storage/Cache, Privacy/Rights, Diagnostics and Settings.<br><br>ENGINE INTERFACES<br>Define canonical interfaces for ASR, Diarization, Translation/LLM, TTS/Voice, Separation, Face Tracking, Lip-Sync, Audio Mix, QC and Render. Engine-specific implementation code must be in adapters.<br><br>DATA<br>Use a local project database (SQLite initially) and an immutable artifact store. Important entities: Project, MediaAsset, Scene, Shot, FaceTrack, SpeakerIdentity, Character, Utterance, TranscriptVersion, TranslationVersion, VoiceProfile, VoiceTake, TimingVersion, LanguageVariant, ConsentRecord, Artifact, Job and QCResult.<br><br>QUALITY<br>Maintain a golden benchmark suite. Record model/provider version, settings, prompt version, latency, quality metrics and hardware. Do not change defaults without benchmark evidence.<br><br>DELIVERY ORDER<br>Foundation -> Media/ASR -> Speakers/Translation -> Voice/Timing -> Audio/Mix/Subtitles -> Professional Timeline/QC -> Visual Lip-Sync -> Packaging/Reliability -> Scale.<br><br>IMPLEMENTATION RULE<br>At the end of every milestone, run unit, contract and integration tests; open the packaged Windows UI; process a short real media fixture end-to-end; verify project recovery; and document remaining gaps before continuing.
```

## 77. Technology Validation Notes (August 2026)

The architecture intentionally uses replaceable adapters because model quality, licensing, hardware requirements and APIs change quickly. Current primary-source validation supports the following directions:

- Qt for Python provides the official PySide6 bindings for Qt and is suitable for building a Python desktop UI.
- faster-whisper is a CTranslate2-based Whisper implementation intended for efficient local transcription.
- pyannote.audio is a Python/PyTorch toolkit for speaker diarization.
- MuseTalk is an audio-driven lip-sync project focused on real-time/high-quality face synchronization.
- LatentSync is an end-to-end audio-conditioned latent-diffusion lip-sync framework.
- Demucs provides source-separation models useful as a fallback when clean production stems are unavailable.
- Open TTS candidates such as Chatterbox, Fish Speech and F5-TTS should be benchmarked per language and license before being enabled by default.
### 77.1 Primary sources to re-check before implementation

| Technology | Primary Source |
| --- | --- |
| Qt for Python / PySide6 | https://doc.qt.io/qtforpython-6/ |
| faster-whisper | https://github.com/SYSTRAN/faster-whisper |
| pyannote.audio | https://github.com/pyannote/pyannote-audio |
| MuseTalk | https://github.com/TMElyralab/MuseTalk |
| LatentSync | https://github.com/bytedance/LatentSync |
| Demucs | https://github.com/facebookresearch/demucs |
| Chatterbox | https://github.com/resemble-ai/chatterbox |
| Fish Speech | https://github.com/fishaudio/fish-speech |
| F5-TTS paper/repository direction | https://arxiv.org/abs/2410.06885 |

## 78. Final Product Positioning

The product should not be positioned as a one-click “translate and replace audio” utility. It should be positioned as a professional Windows AI localization workstation: AI accelerates analysis and first-pass generation, while the editor preserves full human control over language, performance, identity, synchronization, audio and delivery.

> North-star product statement  A Python-only Windows dubbing studio that can analyze once, localize into many languages, preserve characters and cinematic sound, recover from long jobs, and let a professional editor override every AI decision.
