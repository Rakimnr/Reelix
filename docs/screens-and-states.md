# Reelix — Screens and States

## Design Principle
Reelix must not create a separate full screen for every state. The product uses a combination of:
- normal in-app screens
- Android system permission/special-access screens
- floating overlay states
- compact result overlays
- full/detail in-app screens or sheets

The floating bubble remains the product’s primary interaction outside the host app.

---

## 1. Welcome / Onboarding Screen
**Type:** In-app screen

**Purpose:** Explain Reelix before requesting any special access.

**Content:**
- Reelix logo/name
- short value proposition
- simple 3-step visual:
  1. Enable Scanner
  2. Tap bubble on a Reel
  3. Get likely movie/TV match
- Continue button

**State:** First launch only, with optional Help replay later.

---

## 2. Privacy & Scanner Explanation
**Type:** In-app screen

**Purpose:** Give transparent disclosure before screen-capture permission.

**Must explain:**
- scanner uses Android screen-capture permission
- a capture session may remain active while scanner is enabled
- idle frames are discarded/not analyzed
- a short sample is retained only after an explicit scan action
- no scan recording is saved to Gallery/Downloads
- selected evidence may be sent for analysis
- protected content may not be capturable

**Actions:**
- Continue
- Cancel / Not now
- Privacy details

---

## 3. Permission Guidance Screen
**Type:** In-app screen that launches Android-controlled permission/special-access flows

**Permission checklist:**
- Draw over other apps
- Notification permission/status where applicable
- Screen capture session
- Audio permission/capability only if/when audio capture is enabled

**States:**
- Not granted
- Partially granted
- Ready to start scanner
- Permission revoked

Do not imitate Android system permission dialogs with fake custom dialogs.

---

## 4. Home / Scanner Dashboard
**Type:** Main in-app screen

### Scanner Off state
Elements:
- **Start Reel Scanner** primary CTA
- permission status summary
- privacy shortcut
- recent results
- History
- Saved
- Settings

### Scanner Active state
Elements:
- clear **Scanner Active** status
- explanation that Android screen-sharing session is active
- **Stop Scanner** action
- optional **Pause Scanner** only if architecture defines its semantics safely
- recent results
- History
- Saved

### Scanner Error / Revoked state
Elements:
- **Scanner stopped**
- reason if known
- **Start again** CTA

---

## 5. Floating Bubble — Idle
**Type:** System application overlay

**Purpose:** Always-available scan trigger when permitted by Android/current app.

**Properties:**
- small Reelix logo/icon
- draggable
- edge snapping optional
- not visually mistaken for system UI
- tap = Identify Movie/Series
- long-press/expand = menu

**State:** Idle / Ready

---

## 6. Expanded Bubble Menu
**Type:** Overlay

**Actions:**
- Identify Movie / Series
- Check AI Content
- Pause Scanner
- Stop Scanner

Optional secondary action:
- Open Reelix

Keep the menu compact so it does not obstruct the underlying content more than necessary.

---

## 7. Countdown Overlay
**Type:** Overlay

**Purpose:** Prevent accidental capture and give the user a clear chance to cancel.

**Elements:**
- 3 → 2 → 1 countdown
- Cancel / X
- mode label: **Identify** or **AI Check**

**Exit states:**
- Cancelled → Idle
- Completed → Sampling

---

## 8. Sampling State
**Type:** Minimal overlay/bubble state

**Purpose:** Show that screen evidence is actively being collected.

**Visual:**
- pulse/ring/animation around bubble
- short text only if space allows: **Scanning…**

**Requirements:**
- avoid contaminating sampled evidence where technically possible
- no misleading “recording saved” wording

---

## 9. Processing State
**Type:** Bubble / small overlay state

**Visual:**
- spinner or rotating Reelix animation
- label: **Analyzing…**
- optional Cancel when technically meaningful

**Transitions:**
- Strong candidate
- Possible matches
- No match
- Offline
- Capture unavailable
- Error

---

## 10. Unified Compact Result Overlay
**Type:** Overlay attached/near bubble

**Content Structure:**
The overlay should support independent sections/cards for whatever was identified.

**MOVIE / TV**
- poster thumbnail
- title
- year/release information
- possible series/episode information
- wording such as **Strong candidate** or **Likely match**
- match state

**MUSIC**
- song title
- artist
- album/artwork later if available
- match state

**AI CONTENT**
- separate experimental assessment

**Actions:**
- Details
- Save
- Wrong result?
- Dismiss

Do not show an arbitrary AI-generated confidence percentage.

---

## 11. Compact Result — Possible Matches
**Type:** Overlay

**Content:**
- **Possible matches** heading
- 2–3 compact candidate rows
- title/year/poster where available

**Actions:**
- select candidate
- Try Again
- Dismiss

---

## 12. Compact Result — No Match
**Type:** Overlay

**Content:**
- **Couldn’t identify this clip**
- short suggestion to retry with a clearer/longer scene

**Actions:**
- Try Again
- Dismiss

---

## 13. Movie / Series Details
**Type:** In-app full screen, modal sheet, or expanded overlay depending on final UX

**Content:**
- poster
- title
- year/release information
- synopsis
- cast metadata where available
- movie vs series
- available season/episode only when verified
- evidence summary / “Why this match?”
- disclaimer that match is based on a short screen sample

**Actions:**
- Save / Remove from Saved
- Wrong result?
- Close / Back

Future optional:
- where-to-watch links when legally/contractually available

---

## 14. History Screen
**Type:** In-app screen

**Content:**
- previous scan result metadata
- date/time
- title/poster where available
- result type

**Actions:**
- open details
- delete entry
- clear history

**Privacy rule:** No raw captured video, audio, or frames are displayed/stored as history.

---

## 15. Saved / Watchlist Screen
**Type:** In-app screen

**Content:**
- saved titles
- poster/title/year

**Actions:**
- open details
- remove from saved

Initially local-only.

---

## 16. AI-Content Assessment Result
**Type:** Compact overlay with optional detailed view

**Possible primary outcomes:**
- Likely AI-generated
- Possible AI editing / mixed content
- No strong AI-generation evidence detected
- Inconclusive

**Content:**
- result category
- short “Why?” explanation
- evidence observed
- limitations

**Required disclaimer:**
This is an automated assessment and not absolute proof.

**Do not display:**
- “100% real”
- unsupported fake percentages
- “No C2PA = real”

---

## 17. Settings & Privacy Screen
**Type:** In-app screen

Sections:
- Scanner
  - bubble size/position preferences if added
  - start/stop scanner
- Data
  - clear history
  - clear saved items
  - explain temporary evidence handling
- Privacy
  - what is captured
  - what may be uploaded
  - third-party processing disclosure
- Permissions
  - overlay status
  - notification status
  - screen-capture state information
- Help
  - why bubble may disappear on protected apps
  - why audio may be unavailable
  - why some content cannot be captured
- About

---

## 18. Offline Error Overlay
**Type:** Overlay

Message:
**Internet connection required to analyze this scan. Temporary scan data has been discarded.**

Actions:
- Dismiss
- Retry only after a new scan; do not silently retain raw evidence for later upload by default

---

## 19. Permission Revoked / Scanner Stopped Overlay
**Type:** Overlay or host-app state

Message:
**Screen capture stopped. Start the Reelix Scanner again to continue.**

Action:
- Open Reelix / Start Again

---

## 20. Capture-Unavailable / Protected-Content State
**Type:** Overlay

Preferred wording:
**Reelix couldn’t capture usable video from this content. It may be protected or unavailable for screen capture.**

Actions:
- Dismiss
- Try Another Clip

Do not state DRM as a certainty based only on black/unusable frames.

---

## 21. Overlay Blocked / Not Visible Help State
**Type:** In-app help/status

Message concept:
Some apps can block third-party overlays for security. Reelix cannot override that restriction.

Do not attempt to bypass `HIDE_OVERLAY_WINDOWS` or equivalent protections.

---

## 22. Temporary Cleanup Error State
**Type:** Internal/error handling with user-visible message only when necessary

If Reelix cannot confirm cleanup of a private temporary file:
- stop the scan flow
- attempt cleanup again
- record a privacy-safe local diagnostic
- avoid uploading/retaining new evidence until safe state is restored if necessary

---

## 23. State Machine Summary
```text
SCANNER OFF
   │ Enable + Android consent
   ▼
SCANNER ACTIVE / BUBBLE IDLE
   │ tap Identify
   ▼
COUNTDOWN ──Cancel──> IDLE
   │
   ▼
SAMPLING
   │
   ▼
PROCESSING
   ├──> STRONG CANDIDATE ──Dismiss──> IDLE
   ├──> POSSIBLE MATCHES ──Dismiss──> IDLE
   ├──> NO MATCH ──────────Dismiss──> IDLE
   ├──> OFFLINE ───────────Dismiss──> IDLE
   └──> CAPTURE ERROR ─────Dismiss──> IDLE

At any time:
MediaProjection revoked/stopped → SCANNER OFF
```

## 24. Screen vs Overlay Classification
### Standard in-app UI
- Welcome / Onboarding
- Privacy Explanation
- Permission Guidance
- Home / Scanner Dashboard
- Movie/Series Details
- History
- Saved / Watchlist
- Settings & Privacy
- detailed AI assessment view if needed

### Android system-controlled UI
- Draw-over-other-apps special access
- Screen-capture consent
- Notification permission dialog where requested

### Reelix overlays
- Floating Bubble
- Expanded Bubble Menu
- Countdown
- Sampling indicator
- Processing indicator
- Compact identification results
- AI assessment compact result
- error/status overlays
