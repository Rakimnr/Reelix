# Reelix — Implementation Roadmap

## Constraint
**Near-zero initial budget.** Use local development, mocks, emulator tools, and permitted free API tiers only. Do not activate billing, paid APIs, subscriptions, or production cloud deployments without explicit approval.

## Roadmap Principle
The biggest product risk is not the floating bubble itself; it is whether Reelix can identify enough real clips accurately enough to be useful. Therefore recognition feasibility is tested before large UI/platform investment.

---

## MILESTONE 0A — Visual Matching Spike
**STATUS: COMPLETED**

**Achievements:**
- OpenCLIP embeddings working locally
- FAISS reference index working
- Reel degradation simulation working
- 5 indexed clips recovered successfully
- NO_MATCH layer implemented

---

## MILESTONE 0B — Visual Threshold Calibration
**STATUS: COMPLETED / CONTINUING VALIDATION**

**Current calibration:**
- Known: 0.7227–0.8841
- Unknown: 0.6023–0.6925
- No overlap in current small dataset.

**Important:**
No production threshold selected yet.

---

## MILESTONE 0C — OCR Supporting Evidence
**FUTURE**

**Goal:** Test whether subtitle/visible text improves difficult movie/TV matches.

---

## MILESTONE 0D — Local Music Identification Spike
**FUTURE**

**Goal:** Prove that a short audio sample can identify one song from a small local authorized music fingerprint catalogue.

- No cloud.
- No paid API.
- No API key.

The experiment should eventually test:
- clean song sample
- noisy sample
- music under dialogue where possible
- compressed Reel-style audio
- possibly short segments

*Do NOT implement this spike now unless explicitly instructed later.*

---

## Milestone 1 — Project Setup and Architecture Spike
**Goal:** Establish repository structure and validate Flutter + Kotlin boundary.

### Tasks
- Initialize Flutter application.
- Keep Android Kotlin integration enabled.
- Define module/package structure.
- Add local configuration templates with no secrets committed.
- Create a simple native Android overlay spike.
- Compare native overlay vs Flutter-rendered overlay if needed.
- Create a local backend proxy project (FastAPI/Node.js or equivalent) with a mock endpoint.

### Acceptance Criteria
- App builds on target Android device/emulator.
- Reelix can request/verify overlay special access.
- A draggable bubble can appear over another app.
- Architecture decision for bubble implementation is documented.
- Local backend returns a mock response.

---

## Milestone 2 — MediaProjection Lifecycle Spike
**Goal:** Prove the Android 14+ capture-session model before building product UI around it.

### Tasks
- Add privacy rationale screen.
- Implement correct MediaProjection consent flow.
- Start required media-projection foreground service.
- Create one VirtualDisplay for the permitted session.
- Connect to ImageReader/Surface.
- Register `MediaProjection.Callback#onStop()`.
- Implement idle frame dropping/ignoring without retention.
- Test repeated scan triggers using the same active VirtualDisplay.
- Test screen lock, revocation, process death, rotation/configuration change.
- Profile memory/CPU/battery.

### Acceptance Criteria
- 20+ repeated scan triggers can sample from the same active session without creating a new VirtualDisplay per tap.
- No unbounded memory growth while idle.
- Revocation reliably disables scanner state.
- App releases projection resources correctly.
- Battery/CPU observations are documented so Path A can be accepted or rejected.

### Architecture Gate
Decide whether persistent projection is acceptable. If not, switch to consent-per-scan architecture and update UX documents.

---

## Milestone 3 — Core Capture and Cleanup Pipeline
**Goal:** Convert the active projection stream into a short privacy-bounded evidence package.

### Tasks
- Bubble tap → countdown with Cancel.
- Implement approximately 5-second sampler.
- Retain maximum configured number of useful frames.
- Add frame downscaling/compression.
- Add on-device OCR.
- Add optional playback-audio experiment.
- Implement evidence degradation:
  - frames + OCR + audio
  - frames + OCR
  - frames only
- Implement cleanup on:
  - success
  - cancel
  - offline/network failure
  - exception
  - timeout
  - service stop
  - app restart
- Investigate preventing Reelix bubble/countdown from contaminating sampled evidence.

### Acceptance Criteria
- No scan media appears in Gallery/Downloads.
- No raw scan remains as history.
- Temp-cache fallback is deleted in every tested completion/failure path.
- Repeated scans have bounded memory behavior.
- Audio absence does not break identification flow.

---

## Milestone 4 — End-to-End Mock Product Flow
**Goal:** Build the actual Reelix experience before adding a live provider.

### Tasks
- Complete onboarding/privacy/permission guidance.
- Complete Home / Scanner Dashboard.
- Implement bubble states:
  - Idle
  - Countdown
  - Sampling
  - Processing
  - Result/Error
- Implement expanded bubble menu.
- Implement compact result overlay.
- Implement possible matches/no match.
- Implement movie/series details.
- Implement local History.
- Implement local Saved/Watchlist.
- Implement offline, permission-revoked, and capture-unavailable states.
- Use local backend mock to return deterministic fake fixture results for UI testing.

### Acceptance Criteria
User can complete this full flow with mock recognition:

`Open Reelix → Enable scanner → open another app → tap bubble → countdown → sample → process → result → details/save → history → scan again → stop scanner`

No real provider secret is in the APK.

---

## Milestone 5 — Secure Local Backend + Real Recognition Integration
**Goal:** Replace mock recognition with the validated recognition approach while preserving the secret boundary.

### Tasks
- Implement provider adapter interface in local backend.
- Add candidate generation.
- Add metadata verification.
- Add no-match/possible-match rules.
- Add request/evidence size limits.
- Add privacy-safe logging.
- Integrate mobile evidence upload to local backend during development.
- Re-run recognition evaluation through the same backend code path.

### Acceptance Criteria
- Real test clips can be processed end to end.
- Measured accuracy remains consistent with Milestone 0 expectations.
- Provider secret exists only in backend/local environment configuration.
- Wrong-model answers do not automatically become strong UI matches without verification.

---

## Milestone 6 — AI-Content Assessment Experiment
**Goal:** Add the second major Reelix capability without mixing it with identification logic.

### Tasks
- Add **Check AI Content** to expanded bubble menu.
- Reuse privacy-bounded capture pipeline.
- Build separate AI-assessment service interface.
- Return only allowed categories:
  - Likely AI-generated
  - Possible AI editing / mixed
  - No strong AI-generation evidence
  - Inconclusive
- Add evidence explanation and limitations.
- Build a documented ground-truth evaluation set.
- Measure false positives, false negatives, and inconclusive rate.

### Acceptance Criteria
- No “100% real” claim.
- Missing original metadata/C2PA from screen recording is not treated as evidence of authenticity.
- AI-check failure cannot break movie-identification flow.

---

## Milestone 7 — Product Hardening
**Goal:** Prepare the app for broader internal testing.

### Tasks
- Device/API test matrix.
- Battery optimization.
- Memory/leak profiling.
- Overlay behavior across OEMs.
- Accessibility of Reelix UI (not Android Accessibility Service capture).
- Network resilience.
- privacy copy review.
- APK secret inspection.
- log redaction.
- crash handling.
- analytics design only if needed and privacy-approved.

### Acceptance Criteria
- Capture lifecycle tests pass.
- Cleanup tests pass.
- No secrets found in APK.
- App handles projection revocation/process death correctly.
- UX testers understand scanner-active privacy state.

---

## Milestone 8 — Production Backend Decision
**Goal:** Choose infrastructure only after usage/accuracy requirements are known.

### Evaluate
- external multimodal provider
- commercial/licensed ACR provider
- hybrid recognition
- lawful Reelix fingerprint index
- required database/auth/cloud sync
- rate limiting
- abuse protection
- cost per scan

### Zero-budget rule
Do not enable billing merely because a cloud platform is convenient.

For example, Firebase Functions may be developed with the Local Emulator Suite without a Cloud Billing account, while production deployment requires the Blaze plan. Treat production cloud activation as a separate approved decision.

### Acceptance Criteria
A written production architecture decision records:
- provider
- commercial terms
- estimated cost
- privacy/data-use terms
- scaling model
- secrets/security model

---

## Milestone 9 — Google Play / Commercial Readiness
**Goal:** Prepare for internal/closed testing and eventual publication.

### Tasks
- Review current Google Play requirements at release time.
- Complete Data Safety declarations accurately.
- Verify foreground-service declarations/use cases.
- Verify screen-capture and overlay disclosure.
- Add Privacy Policy.
- Finalize terms/provider attribution/licensing.
- Add backend abuse/rate limits.
- Decide whether accounts are actually needed.
- Decide monetization only after cost-per-scan is understood.

### Acceptance Criteria
- Release candidate passes privacy/security checklist.
- Required disclosures match real data flow.
- No billing/monetization claim is enabled accidentally.
- Internal testing build is ready.

---

# Recommended Immediate Next Task
**Start Milestone 0: Recognition Feasibility Spike.**

Do not begin with full visual polish. First prove that a small evidence package can identify enough lawful test clips correctly. In parallel or immediately after that, perform the Android overlay/MediaProjection architecture spike.

# Suggested Repository Shape
```text
reelix/
├─ app/                         # Flutter host app
│  ├─ lib/
│  └─ android/                  # Kotlin native integration
├─ backend/
│  ├─ src/                      # local proxy + provider adapters
│  ├─ tests/
│  └─ .env.example
├─ recognition-evaluation/
│  ├─ manifests/                # test metadata, no unauthorized media
│  ├─ scripts/
│  └─ results/
└─ docs/
   ├─ product-requirements.md
   ├─ user-flows.md
   ├─ screens-and-states.md
   ├─ architecture-options.md
   ├─ validation-plan.md
   └─ implementation-roadmap.md
```
