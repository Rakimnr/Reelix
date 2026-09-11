# Reelix — Architecture Options

## 1. Architecture Principles
The architecture must prioritize four constraints:
1. The floating bubble remains the primary user interaction.
2. No permanent screen recording is created during normal scans.
3. Recognition quality is validated before expensive infrastructure is adopted.
4. Development begins with near-zero cost and no embedded provider secrets.

## 2. Client UI Framework
### Candidate A — Flutter UI + Native Kotlin Capture/Overlay
**Recommended candidate for the first implementation spike.**

**Flutter responsibilities**
- Onboarding
- Home / Scanner Dashboard
- History
- Saved / Watchlist
- Movie/TV details
- Settings & Privacy
- AI-analysis details
- General application UI/state management

**Native Kotlin responsibilities**
- MediaProjection lifecycle
- Foreground service
- VirtualDisplay
- ImageReader / frame sampling
- Optional playback-audio capture
- Native overlay window / bubble if Flutter overlay overhead is too high
- Android-specific lifecycle/revocation handling

**Bridge**
- Flutter Platform Channels (or Pigeon) for communication between Flutter and Android-native components.

**Pros**
- Fast product UI development.
- Keeps difficult Android platform APIs in Kotlin.
- Fits the existing plan to use Flutter for the main application.

**Risks**
- Running an additional Flutter engine for a tiny always-available overlay may consume unnecessary memory.
- Overlay lifecycle can become complex if implemented entirely in Flutter.

### Candidate B — Pure Kotlin + Jetpack Compose
**Pros**
- Single runtime/toolchain for Android.
- Direct access to MediaProjection, services, overlays, and lifecycle APIs.
- Potentially simpler background/overlay memory model.

**Cons**
- Slower if the team is significantly more productive in Flutter.
- Removes cross-platform potential, although Reelix is Android-first anyway.

### Decision Rule
Do not decide by preference alone. Build a small architecture spike and compare:
- memory while scanner is idle
- bubble responsiveness
- lifecycle reliability
- implementation complexity

The default plan is **Flutter for the host app + Kotlin for capture/service/overlay**, unless the spike shows that the Flutter boundary causes unnecessary complexity.

---

## 3. Android Overlay Architecture
The Reelix bubble uses Android application-overlay capability (`SYSTEM_ALERT_WINDOW` / “Draw over other apps”). This is special app access controlled through system settings.

### Important limitation
Some applications may use Android protections that prevent third-party overlays from appearing over them. Reelix must not attempt to bypass these restrictions.

### Bubble implementation options
#### Option 1 — Native Kotlin View/Compose overlay
- Foreground/service-managed WindowManager overlay.
- Lowest overhead candidate for a small bubble.
- Recommended baseline for the architecture spike.

#### Option 2 — Flutter-rendered overlay
- Reuse Flutter widgets/styles.
- Potentially higher memory/runtime cost.
- Validate before choosing.

---

## 4. Critical Platform Investigation — MediaProjection on Android 14+
Official Android behavior for apps targeting Android 14+ requires user consent for each **MediaProjection capture session**. One capture session corresponds to one call to `createVirtualDisplay()`, and the same MediaProjection instance cannot be reused for multiple `createVirtualDisplay()` calls.

Reelix therefore must distinguish:
- **Sampling a short scan from an already active VirtualDisplay**
- **Ending the MediaProjection session itself**

These are not the same operation.

### Path A — Persistent Capture Session with On-Demand Sampling
**Recommended architecture to investigate first because it best matches the Reelix UX.**

Flow:
1. User opens Reelix and taps Enable Scanner.
2. User grants Android screen-capture consent.
3. Reelix starts the media-projection foreground service.
4. Reelix creates one VirtualDisplay for that session.
5. While idle, incoming frames are immediately dropped/ignored and not retained/analyzed.
6. User taps bubble.
7. Reelix samples approximately 5 seconds of evidence from the existing stream.
8. Reelix returns to dropping/ignoring idle frames.
9. Session remains active until the user stops it, the system revokes it, screen/lifecycle behavior ends it, or the process/service dies.

**Advantages**
- Seamless repeated bubble scans without a new consent dialog for every tap while the same capture session remains alive.
- Closest to the Shazam-like Reelix experience.

**Costs/Risks**
- Android shows persistent screen-sharing/capture indicators.
- More battery/GPU work than an inactive session because the OS is maintaining projection output.
- Reelix technically has access to projection frames while enabled, even though idle frames are discarded.
- User disclosure must be precise and transparent.

**Required disclosure concept**
> The scanner session remains active while the Reelix bubble is enabled. Reelix discards idle frames and retains a short sample only after you start a scan.

Do not claim that Reelix has no screen access before the tap if a persistent VirtualDisplay is active.

### Path B — Tear Down Projection Between Every Scan
Flow:
1. No active MediaProjection while bubble is idle.
2. User taps bubble.
3. Reelix starts an Activity to request Android capture consent.
4. User confirms.
5. Reelix creates the VirtualDisplay, scans, and ends the session.

**Advantages**
- Minimal idle screen-access window.
- Potential battery/privacy advantages.

**Disadvantages**
- Android consent interaction is required for each new capture session.
- Significantly less seamless.

### Current Architecture Decision
Use **Path A as the first technical spike**, not as an assumed final answer. Measure battery, memory, lifecycle behavior, and user experience before freezing the decision.

---

## 5. MediaProjection Service Requirements
The Android-native layer must:
- run capture with the required foreground-service type
- start the service in a platform-compliant sequence
- create one VirtualDisplay per MediaProjection session
- register `MediaProjection.Callback#onStop()`
- release VirtualDisplay, Surface/ImageReader, audio resources, and buffers when stopped
- update the bubble to **Scanner Disabled** when projection is revoked
- handle process death and app restart
- tolerate rotation/configuration changes without creating a second VirtualDisplay from the same MediaProjection instance; use supported resize/surface updates where applicable

---

## 6. Frame Sampling Architecture
### Idle state
- ImageReader/Surface may receive frames while the persistent projection session is active.
- Reelix must acquire/drop frames safely so buffers do not back up.
- Do not retain idle frames.
- Do not run recognition/OCR on idle frames.

### Scan state
Recommended first version:
- sample for ~5 seconds
- keep 4–8 useful frames maximum
- downscale/compress before upload
- run OCR locally where possible
- release unused frames immediately

### Bubble self-capture
The implementation should prevent the bubble/countdown UI from contaminating recognition evidence where possible. Options should be investigated rather than assumed, including temporarily hiding/moving the overlay during the selected sampling moments.

---

## 7. Playback Audio Architecture
Playback audio is optional enhancement evidence.

Android playback-capture rules mean source audio may be unavailable depending on:
- source-app target/configuration
- source-app capture policy
- media usage type
- user profile
- protected content

Architecture must degrade gracefully:
1. Frames + OCR + audio
2. Frames + OCR
3. Frames only
4. No usable evidence → cannot analyze

Do not treat audio capture as a mandatory prerequisite for Reelix.

---

## 8. Local Evidence Processing
Preferred order:
1. MediaProjection provides frame stream.
2. Native sampler selects a small bounded set of frames.
3. OCR runs on-device where practical.
4. Optional audio sample/transcript/fingerprint is produced.
5. Evidence package is created.
6. Evidence package is sent to Reelix backend.
7. Frame/audio buffers are released.
8. Any temporary private-cache file is deleted.

### Storage policy
**Preferred:** memory only.

**Fallback:** application-private cache with:
- strict maximum size
- per-scan identifier
- deletion after success/error/cancel/timeout
- startup cleanup for orphaned scan files

No raw sample is written to public Gallery/Downloads.

---

## 9. Identification Architecture Options

### Option 1 — Hybrid Architecture (Reelix Index + Optional AI Fallback)
**Concept**
Extract compact fingerprints (visual/audio) and OCR text locally. The backend searches a Reelix-owned index of mathematical representations (vectors, hashes). If the index yields a high-confidence match, return it. Only if the index fails, optionally fall back to an external Multimodal AI to attempt identification.

**Advantages**
- Fast and cheap for popular, indexed titles.
- Better exact-scene/episode matching.
- Does not rely on expensive third-party APIs for every scan.
- Allows Reelix to own its recognition intelligence incrementally.

**Risks**
- Requires building and hosting a searchable index (e.g., FAISS, `pgvector`).
- Indexing content requires a lawful acquisition strategy (no scraping copyrighted movies).

**Status:** Recommended target architecture. See `recognition-architecture.md` for details.

### Option 2 — External Multimodal Recognition Only
**Concept**
Send the evidence package to an external multimodal AI model (e.g., Gemini, GPT-4o) and ask it to guess the movie for every single scan.

**Advantages**
- No need to build or maintain a scene index initially.

**Risks**
- High hallucination risk.
- Poor exact episode identification.
- Expensive per-scan at scale; not sustainable for a free app.
- Poses privacy concerns by sending all captures to a third party.

**Status:** Deprecated as the primary core architecture. May only be used as a fallback.

### Option 3 — Licensed ACR (Automatic Content Recognition)
**Concept**
Partner with a commercial ACR provider who already maintains a massive movie fingerprint database.

**Advantages**
- Highly accurate out-of-the-box.

**Risks**
- Extremely expensive commercial licensing. Violates the near-zero budget constraint.

**Status:** Rejected for early development phases.

### Recommended Evolution
**Feasibility Spike:** Option 1 (Hybrid) using a tiny local FAISS index with public-domain test clips.
**Production:** Option 1 (Hybrid) with a gradually expanding catalogue based on user demand.

---

## 10. Candidate Verification Layer
A multimodal model response is a candidate generator, not the source of truth.

Backend verification should support:
- top-N candidate generation
- movie/TV metadata lookup
- title/year/cast/plot consistency checks
- OCR/dialogue consistency checks
- optional future fingerprint similarity
- “no result” when evidence is insufficient

Any displayed numerical confidence must come from a measured/calibrated scoring system, not the model’s self-reported confidence.

---

## 11. AI-Content Assessment Architecture
Keep AI-content assessment isolated from the movie/TV identification pipeline.

Normal screen-capture mode can examine:
- temporal consistency
- object/text stability
- motion/geometry artifacts
- lighting inconsistencies
- audio/visual consistency when available

Do not assume original-file C2PA Content Credentials or metadata survive screen recording.

A future direct-file analysis mode could add provenance/metadata validation because it may have access to the original file rather than a screen-rendered copy.

---

## 12. Backend Boundary and Secret Management
### Development
Because the project has a near-zero-budget/no-billing constraint, begin with a **local backend proxy** running on the developer machine.

Possible local choices:
- FastAPI
- Node.js/Express
- Firebase Local Emulator Suite if Firebase-style functions are desired

The Android emulator/device can call the development machine through an appropriate local-network/emulator address during testing.

### Production
Later, deploy a Reelix-controlled backend that:
- holds provider API secrets
- validates requests
- applies abuse/rate limits
- proxies AI/ACR/metadata calls
- normalizes provider responses
- logs only privacy-approved telemetry

Never embed AI/ACR provider secrets in the APK.

### Firebase note
Cloud Functions for Firebase can be tested locally with the Emulator Suite without a Cloud Billing account. Production function deployment requires the Blaze plan. Therefore it must not be activated during the no-billing phase without explicit approval.

---

## 13. Local Persistence
Use an on-device database such as SQLite/Room (or a Flutter SQLite abstraction) for:
- scan result metadata
- saved/watchlist items
- local settings

Do not store raw scan footage as history.

Cloud sync is optional and deferred.

---

## 14. High-Level Component Diagram
```text
┌─────────────────────────────────────────────┐
│                Flutter Host App             │
│ Onboarding • Home • History • Saved • UI   │
└───────────────────┬─────────────────────────┘
                    │ Platform Channel
                    ▼
┌─────────────────────────────────────────────┐
│             Android Native Layer            │
│ Overlay • FGS • MediaProjection • Sampler  │
│ ImageReader • OCR bridge • Audio (optional) │
└───────────────────┬─────────────────────────┘
                    │ minimal evidence
                    ▼
┌─────────────────────────────────────────────┐
│        Reelix Backend Proxy (local first)   │
│ Auth/abuse later • secret management        │
│ candidate generation • verification         │
└───────────────┬─────────────────┬───────────┘
                │                 │
                ▼                 ▼
      Multimodal/ACR       Movie/TV metadata
          provider              provider
```

---

## 15. Unresolved Decisions
1. Native bubble vs Flutter-rendered overlay.
2. Whether the persistent MediaProjection session has acceptable battery cost.
3. Best safe mechanism to exclude Reelix overlays from sampled evidence.
4. Whether playback audio is reliable enough to materially improve recognition.
5. Which recognition provider gives acceptable accuracy/cost/privacy.
6. Whether a licensed ACR/index is needed for production.
7. Whether numerical confidence should be shown at all in v1.
8. Whether AI-content assessment belongs in the first public release or a later experimental release.

---

## 16. Official Technical References
- Media projection: https://developer.android.com/media/grow/media-projection
- Android 14 MediaProjection behavior: https://developer.android.com/about/versions/14/behavior-changes-14
- MediaProjectionManager: https://developer.android.com/reference/android/media/projection/MediaProjectionManager
- Notification runtime permission: https://developer.android.com/develop/ui/compose/notifications/notification-permission
- AudioPlaybackCaptureConfiguration: https://developer.android.com/reference/android/media/AudioPlaybackCaptureConfiguration
- Special app access: https://developer.android.com/training/permissions/requesting-special
- Overlay blocking: https://developer.android.com/security/fraud-prevention/activities
- Firebase Functions: https://firebase.google.com/docs/functions
- Firebase Functions local/deploy setup: https://firebase.google.com/docs/functions/get-started
