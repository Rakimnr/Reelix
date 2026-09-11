# Reelix — Validation Plan

## 1. Validation Philosophy
Reelix has two separate high-risk areas:
1. **Recognition feasibility** — can the system identify clips accurately enough?
2. **Android capture experience** — can the floating-bubble scanner operate reliably, privately, and within current Android restrictions?

Recognition must be tested early rather than waiting until the end of Android implementation.

---

## 2. Milestone 0 — Recognition Feasibility Evaluation
### Goal
Determine whether the near-zero-cost recognition approach is good enough to justify building the full capture experience.

### Test material
Use only lawfully obtained material, for example:
- public-domain video
- Creative Commons material compatible with the test
- footage the team owns/created
- other explicitly licensed/rights-cleared clips

Do not build a test library by scraping copyrighted streaming services.

### Build a controlled test set
Include varied cases:
- clear character/face/location visuals
- no dialogue
- heavy dialogue
- visible subtitles
- subtitles added by a social-media creator
- cropped/zoomed scenes
- vertical reframing
- text overlays/stickers
- low resolution
- color filters
- obscure camera angles
- newer/less-known content where lawful test material exists
- negative examples that are not movies/TV

### Evidence variants
Run the same clips with:
1. frames only
2. frames + OCR
3. frames + OCR + permitted/available audio or transcript

### Metrics
Track:
- Top-1 correct identification rate
- Top-3 candidate recall
- False positive rate
- True negative / correct “No Match” behavior
- hallucination rate
- median/p95 response latency
- approximate API usage/cost per scan if applicable

### Confidence rule
Do not trust a provider/model’s self-reported confidence percentage. If Reelix later displays numeric confidence, create a calibration method based on measured validation data.

### Exit criteria
Do not lock the production recognition provider until results show that the approach is sufficiently useful for the intended product experience.

---

## 3. Overlay / Bubble Validation
Test on multiple Android devices/API levels supported by the project.

Verify:
- special overlay access flow works
- bubble appears after scanner setup
- bubble is draggable
- bubble survives normal app switching
- bubble does not cause severe UI lag
- bubble position is stable after rotation where supported
- bubble handles display-size changes
- bubble menu opens/closes correctly
- overlay-blocking apps are handled without bypass attempts
- service/bubble state remains synchronized with actual scanner state

### Performance metrics
Record:
- idle memory
- active scan memory
- CPU usage
- battery impact during a 30–60 minute scanner-active test
- frame-buffer growth/leaks

---

## 4. MediaProjection Lifecycle Validation
### Consent
- Confirm the official Android capture dialog is used.
- Confirm a new MediaProjection session is not started without required user consent.
- Confirm the implementation never calls `createVirtualDisplay()` twice on the same MediaProjection instance for repeated scans.

### Persistent-session experiment
With one active VirtualDisplay:
- perform 20+ repeated bubble scans
- verify all scans sample from the existing stream
- verify no additional `createVirtualDisplay()` call is used per tap
- verify idle frames are discarded and memory remains bounded

### Revocation
Stop screen sharing from Android system controls.
Expected:
- `MediaProjection.Callback#onStop()` is handled
- VirtualDisplay/Surface/ImageReader/audio resources are released
- scanner state changes to Off/Disabled
- bubble no longer claims it can scan

### Screen lock / unlock
Test:
- lock device while scanner active
- unlock
- observe whether projection survives on each target Android/device combination
- handle either continuation or termination gracefully

### Rotation / configuration change
Verify implementation updates size/surface safely without creating an illegal second VirtualDisplay on the same MediaProjection instance.

### Process death
- force-stop/kill process
- confirm projection session ends as expected
- confirm app restart reports real state rather than stale “Scanner Active” state

---

## 5. Foreground-Service Validation
Verify:
- correct media-projection foreground-service type
- visible/required service notification behavior
- compliant startup sequence
- no illegal background service starts
- service stops and resources release when scanner stops

### Android 13+ notification permission
Test both:
- notification permission allowed
- notification permission denied

Confirm Reelix does not incorrectly treat `POST_NOTIFICATIONS` denial as proof that foreground-service startup itself is forbidden.

---

## 6. Capture and Evidence Validation
### Frame sampling
Verify a ~5-second scan:
- retains only configured number of useful frames
- does not accumulate every frame
- compresses/downscales as designed
- releases discarded frames promptly

### Bubble contamination
Test whether the Reelix overlay appears inside sampled frames.
If yes, evaluate implementation methods for hiding/moving/excluding it during sampling.

### OCR
Test:
- original subtitles
- burned-in subtitles
- creator-added captions
- small text
- multiple languages where supported
- no-text clips

Measure whether OCR improves identification accuracy.

---

## 7. Playback Audio Validation
Test cases:
- source app/content allows playback capture
- source app disallows playback capture
- audio unavailable
- silent clip

Expected:
- Reelix never crashes because audio is unavailable
- frames/OCR path still completes
- UI does not promise audio evidence when it was not captured

---

## 8. Private Storage and Cleanup Validation
### Gallery/Public storage
After repeated scans, inspect:
- Gallery
- Movies
- Downloads
- shared/external storage locations used by the app

Expected: **no Reelix scan video or image appears there.**

### In-memory path
Use Android Studio profiler to verify:
- repeated scans do not create unbounded memory growth
- frame/audio buffers are released after each scan
- idle persistent projection does not leak frames

### Private temporary-cache path
If temp files are required, validate all cases:
- success → file deleted
- no match → file deleted
- network failure → file deleted
- server error → file deleted
- user cancels → partial temp data deleted/not created
- processing timeout → file deleted
- app crash/process death → orphan removed on next startup

### Acceptance wording
Do not claim managed memory is cryptographically “zeroed.” Acceptance is:
- no raw scan remains in persistent/public storage
- temporary files are deleted
- references/buffers are released
- repeated scans show bounded memory behavior

---

## 9. Network / Backend Validation
### Local backend phase
Verify:
- device/emulator can call local Reelix proxy
- no provider API secret exists in mobile code/assets
- mock result flow works end to end

### Failure states
Test:
- offline before scan
- network loss during upload
- timeout
- 4xx
- 5xx
- malformed backend response

Expected:
- raw evidence is discarded after failure
- user gets a clear retry message
- app does not silently retain raw captures for indefinite retry

---

## 10. Security Validation
### APK inspection
Use Android Studio APK Analyzer and/or a lawful local reverse-engineering check of Reelix’s own APK.
Verify no secret provider API keys exist in:
- strings/resources
- manifest
- Flutter assets
- native libraries/config files
- compiled bytecode where practical

### Backend
Before public deployment, test:
- authentication/app attestation strategy if used
- rate limiting/abuse handling
- request size limits
- MIME/content validation
- HTTPS only
- log redaction / no raw evidence in standard logs

### Repository
Verify:
- `.env`/secret files ignored
- no secret committed to Git history
- sample configuration uses placeholders

---

## 11. Result Integrity Validation
Test backend/UI behavior when:
- model gives a plausible but wrong title
- metadata lookup contradicts model answer
- two candidates are equally plausible
- no candidate is reliable
- episode number is unknown

Expected:
- possible matches shown when appropriate
- no-match state allowed
- no fabricated episode/timestamp
- no fabricated numeric confidence

---

## 12. AI-Content Assessment Validation
Build a separate lawful evaluation set containing known-source content where ground truth is documented.

Test categories:
- known synthetic content
- known conventional camera footage
- edited/composited content
- recompressed clips
- screen-recorded content

Measure:
- false AI accusations
- missed synthetic examples
- inconclusive rate

UI acceptance:
- includes **Inconclusive**
- never says “100% real”
- explains evidence and limitations
- does not treat missing C2PA/metadata on a screen recording as proof of authenticity

---

## 13. UX Validation
Test with users on these tasks:
1. Enable scanner for first time.
2. Understand why Android capture permission is requested.
3. Identify a movie/TV clip using bubble.
4. Cancel an accidental scan.
5. Understand scanner-active privacy state.
6. Find History.
7. Save a result.
8. Run AI-content check from expanded bubble menu.
9. Stop scanner completely.

Measure:
- task completion
- time to first scan
- permission confusion
- accidental scans
- whether users understand that scanner session is active while bubble is enabled

---

## 14. Device/API Test Matrix
At minimum test:
- oldest Android version Reelix officially supports
- Android 13
- Android 14
- current target/latest Android available during release preparation
- at least one Samsung device if possible
- at least one Pixel/AOSP-like device if possible
- low/mid-range device for memory/battery behavior

Do not assume one OEM’s overlay/background behavior represents all Android devices.

---

## 15. Release Gates
### Gate A — Recognition Feasible
Recognition test set shows useful accuracy and controlled hallucination/no-match behavior.

### Gate B — Capture Stable
Persistent scanner can run/repeat scans without leaks/crashes and handles revocation correctly.

### Gate C — Privacy Cleanup Verified
No raw capture remains in public storage; temp cleanup passes all failure tests.

### Gate D — Security Verified
No secrets in APK/repository; backend boundary ready.

### Gate E — UX Understandable
Users can enable, scan, understand privacy state, and stop scanner without assistance.

Only after these gates should Reelix move toward a public/internal Play testing track.
