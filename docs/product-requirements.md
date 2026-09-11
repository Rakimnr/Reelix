# Reelix — Product Requirements

## 1. Product Overview
Reelix is an Android-first application that helps users identify movies, TV series, and music appearing in short-form social-media videos without requiring them to manually save the Reel or upload a full recording.

The main Reelix product concept is:
*"Tap Reelix on a Reel to identify what you are watching, what you are hearing, and optionally assess whether the content may be AI-generated."*

The primary interaction is a floating, draggable Reelix bubble displayed over supported apps. After the user explicitly enables a screen-capture session, they can tap the bubble when an unknown scene or song appears. Reelix temporarily samples a short portion of the visible screen and playback audio, extracts useful evidence, analyzes it across independent recognition branches (Movie/TV and Music), displays likely matches, and discards the raw capture data.

Reelix also includes an optional experimental feature that assesses whether a social-media video may contain AI-generated or heavily AI-edited content. This feature must communicate uncertainty and must never present an unsupported “100% real/fake” verdict.

## 2. Product Goals
1. Make movie/TV identification from Reels extremely fast.
2. Keep the floating bubble as the central interaction.
3. Avoid permanent screen-recording files on the user’s phone.
4. Preserve privacy by retaining only the minimum evidence needed for a scan.
5. Validate recognition accuracy before investing in expensive infrastructure.
6. Start with a near-zero development budget.
7. Keep the architecture capable of evolving into a commercial Google Play application.

## 3. Target Audience
Users who frequently consume Instagram Reels, TikTok, YouTube Shorts, Facebook Reels, and similar short-form video content and encounter movie or TV scenes that are not properly credited.

## 4. Core User Experience
1. User launches Reelix.
2. Reelix explains how the scanner works and what screen data may be processed.
3. User taps **Enable Scanner**.
4. Reelix guides the user through Android’s required system permissions/special access.
5. User grants MediaProjection consent for a capture session.
6. A draggable floating Reelix bubble appears.
7. User opens a social-media app.
8. User sees an unknown movie/TV scene.
9. User taps the Reelix bubble.
10. Reelix displays a short countdown with **Cancel**.
11. Reelix samples approximately 5 seconds of screen data from the already-active capture session.
12. Reelix extracts useful evidence such as selected frames, visible subtitle text, and permitted playback audio.
13. Reelix sends only the evidence required for identification.
14. Reelix displays a compact result overlay.
15. User may open details, save the title, dismiss the result, mark it wrong, or try again.
16. Temporary raw capture data is released/deleted after the scan completes or fails.

**Important:** Manual uploads may be added later as a fallback or testing tool, but they must not replace the floating-bubble experience as the primary product interaction.

## 5. Bubble Interaction Requirements
### 5.1 Default Interaction
- **Single tap:** Identify Movie / TV Series.
- The bubble must be draggable.
- The bubble must remain small and unobtrusive while idle.

### 5.2 Expanded Bubble Menu
A long-press or dedicated expand affordance may expose:
- Identify Movie / Series
- Check AI Content
- Pause Scanner
- Stop Scanner

The exact gesture must be validated during UI testing, but the movie/TV identification action must remain the fastest action.

## 6. Capture and Privacy Core Rules
- **No permanent local recording:** Never save scan recordings to Gallery, Downloads, Movies, or shared storage.
- **No raw-capture history:** History stores result metadata only, not captured footage.
- **Bounded processing:** Prefer a bounded in-memory frame/audio buffer.
- **Private temporary cache fallback:** If a library/device requires a temporary file, use app-private cache only, enforce a short lifetime and size limit, and delete it after success, failure, cancellation, timeout, or next app startup.
- **No continuous retained recording:** A persistent MediaProjection session may remain active for seamless repeated scans, but Reelix must discard/ignore idle frames and must not retain or analyze them until the user starts a scan.
- **Transparent disclosure:** Do not claim that Reelix has zero screen access while a persistent projection session is active. Explain that the capture session is active but idle frames are discarded and a sample is retained only after an explicit scan action.
- **No Accessibility Service bypass:** Do not use Accessibility Service to bypass capture, overlay, DRM, or platform protections.
- **Respect protected content:** Never attempt to bypass DRM or secure-window restrictions.
- **Provider transparency:** Explain when selected evidence is uploaded to a third-party provider. Do not promise provider-side zero retention unless the provider terms have been verified.
- **Sensitive-screen safety:** Reelix should not intentionally analyze payment, password, private-message, authentication, or other obviously sensitive screens.

## 7. Android Platform Requirements
### 7.1 Overlay
The floating bubble requires Android “draw over other apps” special access (`SYSTEM_ALERT_WINDOW`). This is special app access, not a normal runtime permission.

Some applications can block third-party overlays. If the bubble disappears over a protected/sensitive app, Reelix must treat that as an operating-system/application restriction rather than attempting to bypass it.

### 7.2 MediaProjection
For apps targeting Android 14+:
- User consent is required for each MediaProjection capture session.
- One `MediaProjection` instance is used for one `createVirtualDisplay()` call.
- Reelix must register and handle `MediaProjection.Callback#onStop()`.
- The media-projection capture session must run with the appropriate foreground-service type.

For seamless repeated bubble scans, Reelix should investigate maintaining a single permitted `VirtualDisplay` session while the scanner is enabled, then sampling evidence only after the user taps the bubble.

### 7.3 Notifications
On Android 13+, `POST_NOTIFICATIONS` can be requested so the foreground-service notification appears normally in the notification drawer. It is **not itself required to start a foreground service**, although a foreground service still must provide its required notification.

### 7.4 Playback Audio
Playback-audio capture is optional evidence and must not be assumed to work for every app.
- Reelix must request/declare the permissions required by Android for audio capture where applicable.
- The source app/content may disallow playback capture.
- Reelix must continue with frames/OCR when audio is unavailable.

## 8. Evidence Extraction Pipeline
A normal scan should use the minimum useful evidence instead of producing a permanent video file.

Recommended pipeline:
1. User starts scan.
2. Bubble/countdown UI is excluded or hidden from sampled evidence where practical.
3. Collect approximately 5 seconds of frames from the active capture session.
4. Select approximately 4–8 useful frames.
5. Compress selected frames.
6. Run on-device OCR on visible text/subtitles.
7. Capture a short playback-audio buffer when Android and the source app allow it.
8. Optionally generate local fingerprints/embeddings later.
9. Send only required evidence to the identification backend.
10. Release frame/audio buffers and delete any private temp file.

### Evidence Degradation Strategy
- Frames + OCR + permitted audio → strongest evidence package
- Frames + OCR → normal evidence package
- Frames only → reduced evidence package
- No usable visual data → cannot analyze this content

## 9. Identification Requirements
Reelix should combine multiple signals rather than trusting one model output.

Potential signals:
- Visual frames
- Subtitle/OCR text
- Dialogue/transcript when available
- Permitted audio fingerprint/features
- Movie/TV metadata used to verify candidates
- Future licensed scene/fingerprint index

### Result Rules
- Return one strong candidate, several possible candidates, or **Unable to identify**.
- Do not accept the first AI response blindly.
- Do not fabricate exact episode numbers, timestamps, actor names, or confidence percentages.
- Any numeric “confidence” shown to users must be based on an evaluated and calibrated scoring method.
- Provide a **Wrong result?** feedback action.

## 10. Identification Architecture Strategy
### Phase A — Near-Zero-Cost Validation
Do not build a massive movie-scene database initially.

Use:
- selected visual frames
- OCR text
- optional permitted audio/transcript
- a multimodal recognition service for candidate generation
- a movie/TV metadata service for candidate verification

### Phase B — Production Accuracy
If validation shows that external AI alone is not accurate enough, evaluate:
- licensed Automatic Content Recognition (ACR) providers
- licensed/reference fingerprint datasets
- an owned index of lawful/licensed fingerprints or embeddings
- a hybrid system: index search first, AI fallback second

Do not scrape or download copyrighted films/streaming content to construct an unauthorized recognition index.

## 11. AI-Content Assessment Requirements
AI-content assessment is a separate experimental capability.

Possible outcomes:
- Likely AI-generated
- Possible AI editing / mixed content
- No strong AI-generation evidence detected
- Inconclusive / unable to determine

Rules:
- Never claim “100% real.”
- Absence of evidence is not proof that content is genuine.
- A screen capture usually does not preserve the original media file’s provenance metadata or Content Credentials, so C2PA/metadata checks cannot be assumed to work on ordinary Reelix screen captures.
- If Reelix later supports direct file import or source-media analysis, provenance checks may become more useful.
- Results must explain the evidence/limitations rather than showing only a fake percentage.

Potential evidence layers:
- frame-to-frame visual consistency
- temporal artifacts
- unstable text/object geometry
- lighting/motion inconsistencies
- audio/visual consistency where audio is available
- provenance/metadata only when genuinely available from the analyzed source

## 12. Main Product Surfaces
Reelix should define the following screens, overlays, and states:
1. Welcome / onboarding
2. Privacy explanation
3. Permission guidance
4. Home / Scanner Dashboard
5. Floating bubble — idle
6. Expanded bubble menu
7. Countdown / cancel overlay
8. Sampling state
9. Processing state
10. Compact identification result
11. Possible-matches / no-match result
12. Movie/Series details
13. History
14. Saved / Watchlist
15. AI-content assessment result
16. Settings & Privacy
17. Offline state
18. Permission-revoked state
19. Capture-unavailable/protected-content state

Not every item is a separate Activity. Many should be overlay states, bottom sheets, or in-app views.

## 13. Local Data Requirements
Initially store locally:
- user preferences
- scanner settings
- identification history metadata
- saved/watchlist titles
- user feedback pending upload, if applicable

Do **not** store:
- raw scan video
- raw captured frames as history
- raw audio as history

A mandatory account is not required for the first version.

## 14. Backend and Security Constraints
- **Near-zero initial budget:** No paid service, billing-enabled cloud deployment, subscription, or paid API may be activated without explicit approval.
- During early development, use a **local development backend/proxy** on the developer machine or emulator-compatible local service.
- Provider API keys must never be embedded in the APK, Flutter assets, public repository, or mobile source code.
- Production architecture must place secret-bearing provider requests behind a Reelix-controlled backend boundary.
- Backend requests must use HTTPS in production.
- Production endpoints need authentication/abuse controls before public release.

## 15. Commercial and Licensing Requirements
Before Google Play release, document:
- recognition-provider commercial terms
- movie metadata API commercial terms
- AI-provider data retention/usage terms
- quotas and cost per scan
- Google Play requirements relevant to screen capture, foreground services, overlays, data safety, subscriptions, and advertising

## 16. MVP Success Question
The first product-risk question is:

> Can Reelix identify enough real social-media movie/TV clips accurately enough that users would choose to use it repeatedly?

The Android bubble experience is essential to the final product, but recognition feasibility must be validated early so development effort is not spent polishing an interaction around an unreliable recognition engine.

## 17. Non-Goals for the Initial Build
- Identifying every film/episode ever produced
- Guaranteed exact-scene timestamps
- Guaranteed AI-generated/real verdicts
- Paid subscriptions
- Ads
- Mandatory accounts
- Cloud synchronization
- Building an unauthorized movie-footage database

## 18. Official Technical References
- Android MediaProjection: https://developer.android.com/media/grow/media-projection
- Android 14 MediaProjection behavior changes: https://developer.android.com/about/versions/14/behavior-changes-14
- MediaProjectionManager API: https://developer.android.com/reference/android/media/projection/MediaProjectionManager
- Notification runtime permission: https://developer.android.com/develop/ui/compose/notifications/notification-permission
- Audio playback capture: https://developer.android.com/reference/android/media/AudioPlaybackCaptureConfiguration
- Special permissions / Draw over other apps: https://developer.android.com/training/permissions/requesting-special
- Overlay blocking / HIDE_OVERLAY_WINDOWS: https://developer.android.com/security/fraud-prevention/activities
