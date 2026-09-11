# Milestone 1: Android Capture Architecture Spike

## Overview
This spike validates the technical feasibility of capturing short screen evidence (visual) and playback audio evidence from a backgrounded Android application (e.g., Instagram or TikTok) using a floating bubble overlay.

## Flutter / Kotlin Boundary
- **Flutter (`main.dart`)**: Serves as the debug UI for requesting permissions (Overlay, Notification, Record Audio) and checking their status.
- **MethodChannel (`com.reelix.reelix/scanner`)**: Bridges Flutter and native Android. Flutter calls methods like `requestOverlayPermission` or `startScanner`.
- **Kotlin (`MainActivity.kt` & `ScannerService.kt`)**: Handles the Android native complexities (MediaProjection token lifecycle, Foreground Service, WindowManager overlay, ImageReader, and AudioPlaybackCapture).

## Permissions Used
- `SYSTEM_ALERT_WINDOW`: For the floating "🎥" bubble overlay.
- `FOREGROUND_SERVICE` / `FOREGROUND_SERVICE_MEDIA_PROJECTION`: Required to run a screen capture session.
- `RECORD_AUDIO`: Required to use `AudioPlaybackCapture`.
- `POST_NOTIFICATIONS`: For Android 13+ to display the foreground service indicator.

## MediaProjection & Overlay Lifecycle
1. **Request**: `MainActivity` requests `createScreenCaptureIntent()`.
2. **Acceptance**: User accepts the system dialogue.
3. **Start**: The resulting intent data is passed to `ScannerService`, starting it as a Foreground Service with type `mediaProjection`.
4. **Overlay**: `ScannerService` uses `WindowManager` to spawn the bubble.
5. **Capture Tap**: When tapped, the service uses the projection token to spin up a temporary `VirtualDisplay` and an `AudioRecord` session on a background thread.
6. **Revocation**: If the user revokes projection from the system UI, `MediaProjection.Callback.onStop()` automatically triggers cleanup and stops the service.

## AudioPlaybackCapture Behavior
- Minimum API 29 (Android 10) enforced.
- Configured to capture `USAGE_MEDIA`, `USAGE_GAME`, and `USAGE_UNKNOWN`.
- Honors source application's `allowAudioPlaybackCapture` flag.
- Silently drops audio (or returns empty/zeroed buffers) if the target app prohibits capture, returning `AUDIO_BLOCKED_OR_SILENT`.

## Temporary Data Policy
- Raw visual frames and audio chunks are meant to be held entirely in memory during the capture window.
- Any temporary debug files written to `cacheDir` (prefixed with `reelix_temp`) are wiped immediately after the bubble tap resolves, or upon `ScannerService` destruction.

## Unresolved Issues & Limitations
- **Current Blocker**: The Antigravity execution environment cannot directly interface with a physical Android device via ADB to run the `flutter run` validation. The code is completely implemented, but physical verification is deferred to the host machine.
- Protected content (DRM, secure windows) will yield black frames in `ImageReader`. This is handled gracefully as "no visual evidence."
