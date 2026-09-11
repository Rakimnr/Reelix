# Reelix Updated Blueprint

This folder contains the revised planning set for Reelix after reviewing the original Antigravity/Gemini planning documents against the original Reelix research and current Android platform documentation.

## Files
- `product-requirements.md`
- `architecture-options.md`
- `user-flows.md`
- `screens-and-states.md`
- `validation-plan.md`
- `implementation-roadmap.md`

## Main revisions
- Corrected Android 13+ notification-permission wording.
- Clarified Android 14+ MediaProjection capture-session rules.
- Reframed the “always-on” option as a persistent capture session with on-demand sampling.
- Added accurate privacy wording for persistent screen projection.
- Added explicit playback-audio degradation behavior.
- Added overlay special-access and overlay-blocking limitations.
- Added complete AI-content-check user flow and UI states.
- Expanded the missing full-app screens/states.
- Moved recognition feasibility to Milestone 0.
- Replaced early production cloud deployment with a local backend/proxy during the no-billing phase.
- Replaced unrealistic “memory proven zeroed” acceptance wording with testable cleanup/memory requirements.
- Strengthened recognition evaluation, security, privacy, device, and lifecycle validation.
