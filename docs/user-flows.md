# Reelix — User Flows

## 1. First Launch / Onboarding
1. User launches Reelix.
2. Reelix presents a short product introduction:
   - identify movies/TV from social-media clips
   - use a floating bubble
   - scan only after an explicit user action
3. User continues to **Privacy & Scanner Explanation**.
4. Reelix explains:
   - Android screen capture is required
   - a persistent capture session may stay active while the scanner is enabled
   - idle frames are discarded/not analyzed
   - only a short scan sample is retained after the user starts a scan
   - no raw recording is saved to Gallery/Downloads
   - selected evidence may be uploaded for analysis
5. User taps **Enable Scanner**.

## 2. Permission / Special-Access Setup
Reelix guides the user through required Android-controlled steps in a clear order.

### 2.1 Draw Over Other Apps
1. Reelix explains why the floating bubble needs overlay access.
2. User opens Android’s special-access screen.
3. User grants **Draw over other apps** for Reelix.
4. User returns to Reelix.

### 2.2 Notification Permission (Android 13+ where applicable)
1. Reelix may request `POST_NOTIFICATIONS` so foreground-service notifications appear normally.
2. If the user denies it, Reelix must not falsely say that a foreground service cannot be started solely because of this denial.
3. Reelix continues according to actual platform behavior and clearly explains any notification visibility limitation.

### 2.3 Screen Capture Consent
1. User taps **Start Scanner**.
2. Android displays the official MediaProjection capture dialog.
3. User approves screen capture.
4. Reelix starts the media-projection foreground service.
5. Reelix creates one VirtualDisplay for that capture session.
6. Bubble appears.
7. Home shows **Scanner Active**.

If the user denies screen capture, Reelix shows a clear explanation and returns to **Scanner Off** state.

## 3. Scanner Active / Idle Flow
1. User leaves Reelix and opens Instagram, TikTok, YouTube, Facebook, or another app.
2. Reelix bubble remains visible when Android/the current app permits overlays.
3. MediaProjection session remains active while the scanner is enabled if the persistent-session architecture is selected.
4. Reelix immediately discards/ignores idle frames.
5. Reelix does not run recognition until the user triggers a scan.

## 4. Main Movie / TV Identification Flow
1. User sees an unknown movie/TV scene.
2. User taps the Reelix bubble once.
3. Reelix displays a short countdown, for example **3 → 2 → 1**, with a visible **Cancel** action.
4. If the user does not cancel, Reelix enters **Sampling** state.
5. Reelix temporarily hides/moves its own overlay from sampled evidence where the implementation permits.
6. Reelix samples approximately **5 seconds** from the active capture stream.
7. Reelix keeps only a small bounded evidence set, for example 4–8 useful frames.
8. Reelix runs on-device OCR on visible text/subtitles.
9. Reelix captures permitted playback audio when available.
10. Reelix builds a minimal evidence package.
11. Bubble changes to **Processing** state.
12. Evidence is sent to the Reelix backend for analysis.
13. Backend generates candidate titles and verifies them using available evidence/metadata.
14. Backend returns one of:
    - strong candidate
    - several possible candidates
    - no reliable match
15. Reelix displays the Compact Result Overlay.
16. Raw frame/audio buffers are released and any temp cache file is deleted.
17. Bubble returns to idle after the result is dismissed.

## 5. Identification Evidence Degradation Flow
### Best case
`Frames + OCR + permitted audio → analysis`

### Audio unavailable
`Frames + OCR → analysis`

### OCR unavailable / no readable text
`Frames → reduced-evidence analysis`

### No usable visual evidence
`No analysis → “Reelix couldn’t capture usable video from this content.”`

Do not automatically claim DRM solely because frames are black/unusable.

## 6. Compact Result Flow — Strong Candidate
Compact result includes:
- poster thumbnail
- title
- year / release information where available
- match wording such as **Strong candidate** rather than an uncalibrated fake percentage
- Details
- Save
- Wrong result?
- Dismiss

### Actions
**Details** → open Movie/Series Details.

**Save** → store title metadata in local Saved/Watchlist.

**Wrong result?** → collect correction feedback without retaining raw scan footage.

**Dismiss** → close result and return bubble to Idle.

## 7. Possible-Matches Flow
When evidence does not justify one answer:
1. Result overlay says **Possible matches**.
2. Show up to a small number of candidates.
3. User may select a candidate, open details, retry, or dismiss.
4. Do not invent certainty.

## 8. No-Match Flow
1. Backend reports insufficient evidence/no reliable match.
2. Reelix shows **Couldn’t identify this clip**.
3. Actions:
   - Try Again
   - Dismiss
4. Optional helper text may suggest letting the scene play a little longer before retrying.

## 9. Cancel Flow
### Cancel during countdown
1. User taps Cancel.
2. Scan never begins.
3. No scan evidence is uploaded.
4. Bubble returns to Idle.

### Cancel during sampling/processing
If technically supported:
1. Stop collection/upload as soon as practical.
2. Release buffers/delete temp files.
3. Return bubble to Idle.
4. Do not keep partial raw evidence as history.

## 10. Expanded Bubble Menu Flow
User long-presses or expands the bubble.

Menu:
- **Identify Movie / Series**
- **Check AI Content**
- **Pause Scanner**
- **Stop Scanner**

The exact gesture/control is a UI decision to validate, but these actions must be clearly separated.

## 11. AI-Content Assessment Flow
1. User opens the expanded bubble menu.
2. User selects **Check AI Content**.
3. Reelix displays countdown + Cancel.
4. Reelix samples approximately 5 seconds using the same privacy/capture rules.
5. Reelix extracts temporal visual evidence and available audio evidence.
6. Reelix processes the sample with the AI-assessment pipeline.
7. Reelix displays one of:
   - Likely AI-generated
   - Possible AI editing / mixed content
   - No strong AI-generation evidence detected
   - Inconclusive
8. Result includes a short evidence explanation and limitations.
9. Result must not say “100% real”.
10. Raw evidence is cleared according to the same cleanup rules.

### Provenance limitation
Normal Reelix screen capture usually does not contain the original media file’s C2PA/metadata. Do not show “No Content Credentials → therefore real.”

## 12. History Flow
1. User opens Reelix Home.
2. User taps **History** or views Recent Results.
3. Reelix shows previous result metadata only:
   - title
   - poster reference/cache where permitted
   - date/time of scan
   - result type (identified / possible matches / no match)
4. User can open details or delete a history entry.
5. Raw scan frames/audio are never shown because they are not retained as history.

## 13. Saved / Watchlist Flow
1. User taps Save from a result/details screen.
2. Reelix stores title metadata locally.
3. User opens Saved/Watchlist.
4. User can open details or remove an item.

Cloud synchronization is not required initially.

## 14. Stop Scanner Flow
1. User selects **Stop Scanner** from Home or bubble menu.
2. Reelix stops the MediaProjection session.
3. Reelix releases VirtualDisplay/Surface/ImageReader/audio resources.
4. Foreground service stops according to platform requirements.
5. Bubble disappears.
6. Home state becomes **Scanner Off**.
7. A later restart of the scanner begins a new MediaProjection capture session and therefore requires Android’s required consent again.

## 15. Pause Scanner Flow
Pause behavior must be explicitly defined during the architecture spike.

Preferred safe interpretation:
- **Pause sampling/interaction while preserving the same permitted projection session only if technically/policy acceptable.**
- Idle frames continue to be discarded.
- UI must still indicate that the screen-sharing session remains active.

If a true pause requires ending MediaProjection, then resuming creates a new capture session and requires new consent. Do not fake a “paused” state that hides an active projection from the user.

## 16. Permission Revoked / Projection Stopped
1. User/system stops screen sharing or `MediaProjection.Callback#onStop()` fires.
2. Reelix immediately releases projection resources.
3. Bubble changes to/briefly shows **Scanner Disabled**, then disappears or becomes non-scanning according to final UI.
4. Home shows **Scanner Off / Permission Required**.
5. User must start a new scanner session to continue.

## 17. Overlay Unavailable Flow
If Android/the foreground app blocks application overlays:
1. Reelix does not attempt to bypass the restriction.
2. If possible, Home/notification can explain that the bubble may not appear over protected apps.

## 18. Offline Flow
1. User starts a scan while no usable network is available.
2. Reelix may complete local extraction, but it must not retain raw evidence for later background upload by default.
3. Evidence is discarded.
4. Show **Internet connection required to analyze this scan**.
5. User may retry after reconnecting.

## 19. Capture-Unavailable / Protected-Content Flow
1. Reelix receives no useful visual frames or a consistently unusable capture.
2. Stop analysis early where possible.
3. Show:
   **Reelix couldn’t capture usable video from this content. It may be protected or unavailable for screen capture.**
4. Do not attempt to bypass the restriction.

## 20. Process Death / Restart Cleanup Flow
On application startup:
1. Inspect Reelix private temp-cache scan directory.
2. Delete orphaned scan files left by abnormal termination.
3. Reset transient scan state.
4. Do not pretend a previous MediaProjection session is still valid.
5. Home shows actual scanner state.

## 21. Result Feedback Flow
1. User taps **Wrong result?**.
2. Reelix offers lightweight choices such as:
   - Wrong movie/series
   - Couldn’t recognize when it should have
   - Other
3. Store/send only the minimum feedback required.
4. Do not automatically upload previously deleted raw footage.

## 22. Repeated Scans
While the same persistent MediaProjection session remains active:
- each bubble tap starts a new short sampling operation
- do not create a second VirtualDisplay from the same MediaProjection instance
- reuse the existing stream for sampling

If the MediaProjection session has ended:
- a new scan session requires the user to start/re-authorize capture according to Android requirements.
