# Reelix Music Recognition Architecture

## 1. Feature Goal
Identify the background song or primary music track playing in a short-form social-media video (Reel) simultaneously alongside the Movie/TV visual recognition.

## 2. User Experience
The user does **not** need a separate app or a second floating bubble. 
The SAME Reelix floating bubble triggers ONE temporary sample that provides evidence for multiple analysis branches. The final result overlay presents independent Movie/TV, Music, and AI Content cards simultaneously.

## 3. Music vs Movie-Audio Distinction
A Reel may contain:
- Original movie dialogue
- Original movie soundtrack
- Unrelated trending music added by the creator
- A remix, or slowed/reverbed music
- Voice-over on top of music

Because a Harry Potter edit might contain a completely unrelated TikTok song, **Music identification must not be assumed to prove the movie identity.** The results must remain entirely independent evidence branches.

## 4. Audio Fingerprint Concept
Unlike sending raw audio to an AI model, acoustic fingerprinting converts a short audio sample into a robust hash (e.g., using algorithms like Chromaprint). This hash resists noise, compression, and slight timing shifts, allowing it to be matched against a database of known audio hashes.

## 5. Local Prototype Architecture
For the near-zero-budget development phase, Reelix will use a small **LOCAL** test catalogue of legally available/authorized music.
- **Capture**: Extract a short playback audio buffer from the screen-sharing session (when permitted).
- **Fingerprint**: Generate a local audio hash.
- **Match**: Search against a small local database of authorized test songs.

*No cloud, no paid APIs, no API keys will be used for prototyping.*

## 6. Clip-Level Audio Matching vs True Song Identification
**IMPORTANT DISTINCTION:**
During initial validation (Milestone 0D/0D.1), we use the mixed audio extracted directly from edited MP4 videos (which may contain music + dialogue + effects). If a query fingerprint matches an indexed fingerprint from these MP4s, it merely proves: **"This query audio matches the audio found in this specific edited video clip."**

It does **NOT** automatically prove: **"This song is Song X by Artist Y."**

Actual song-title identification requires either:
- A reference catalogue containing purely the song's clean audio, indexed with track title/artist metadata.
- Or querying a licensed external music catalogue/provider.

Do not mislabel clip-level audio matching as full song identification in the final product.

## 7. Reference Catalogue Requirement
A fingerprint algorithm alone cannot recognize arbitrary music unless reference fingerprints exist. Reelix must build or license an index that maps fingerprints to song metadata (Title, Artist, Album).

## 8. Audio Capture Limitations
- Playback-audio capture is supported on Android 10+, but the source app (e.g., Netflix, certain social media apps) may block capture.
- If audio is unavailable, Music identification fails gracefully, while Movie recognition continues using visual/OCR evidence.

## 9. Edited/Remixed/Slowed Audio Considerations
Social media content frequently alters original tracks (speed shifts, reverb, pitch changes, bass boosts). Standard acoustic fingerprinting often struggles with these transformations. Future enhancements may need to address robust matching for altered audio.

## 10. Privacy
- The audio buffer must be bounded and temporary.
- No continuous audio recording is saved.
- Captured audio must only be used for generating fingerprints and never stored as raw files in history or Gallery.

## 11. Future Production Options
A. **Reelix-owned licensed/reference music fingerprint catalogue**: We host the fingerprints.
B. **Licensed external music-recognition provider**: Partnering with a commercial ACR service.
C. **Hybrid approach**: Local cache of trending song hashes + fallback to external provider.

*If a third-party recognition service is used later, credentials must stay behind a Reelix-owned backend. The final Reelix user must NEVER be required to enter an API key.*

## 12. Cost/Licensing Concerns
Music databases are heavily protected by copyright. Using a commercial ACR provider is often prohibitively expensive for a free app. Reelix must carefully evaluate the cost per scan before committing to a production architecture.

## 13. Integration with Reelix Movie Recognition
**Unified Request**: The backend receives a unified evidence package (frames + OCR text + audio sample).
**Parallel Processing**: The audio sample routes to the Music Branch, while frames/OCR route to the Movie/TV Branch.
**Unified Response**: The backend returns the best matches for both independently.

## 14. Unresolved Decisions
- Which open-source fingerprinting library to use for the local prototype (e.g., Chromaprint/fpcalc, Dejavu).
- How to handle trending "TikTok remixes" that aren't in standard commercial databases.
- Whether to run audio fingerprint generation directly on the Android client (to save upload bandwidth) or entirely on the backend.

## 15. Recommended Future Music-Identification Spike (Milestone 0D)
**Goal:** Prove that a short audio sample can identify one song from a small local authorized music fingerprint catalogue.
**Test Cases:**
- Clean song sample
- Noisy sample
- Music under dialogue
- Compressed Reel-style audio
- Very short segments (e.g., 2-5 seconds)
