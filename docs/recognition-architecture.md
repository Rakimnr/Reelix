# Reelix Recognition Architecture

The Reelix backend utilizes a flexible, provider-based architecture to independently process visual and audio evidence from the mobile app without requiring continuous updates to the Android/Flutter layer.

## High-Level Flow

Capture (Android App)
  ↓
Frame Selector
  ↓
Local Movie Provider
  ↓ if inconclusive
Google Web Movie Provider [disabled until explicitly enabled]
  ↓
Candidate Extractor
  ↓
TMDb Resolver
  ↓
Movie result

Audio
  ↓
Local Fingerprint
  ↓ if inconclusive
AudD Provider [disabled until explicitly enabled]
  ↓
Music result

## Component Roles

- **Frame Selector**: Selects the single most information-rich frame (based on sharpness, text, etc.) from the 5-frame burst to minimize external API costs.
- **Candidate Extractor**: Deterministically (no LLM) trims noise, deduplicates case-insensitively, and removes generic stop-words from external evidence.
- **TMDb Resolver**: Uses the best extracted candidate title to search for canonical metadata. It is metadata/search only, not screenshot recognition.
- **External Providers**: `google_web_movie` and `audd_music` are placeholders. **No cloud API should run without explicit configuration.** Currently they remain OFF by default and return `SKIPPED`.

## Local Index Limitations
The current `local_index` movie provider recognizes **only indexed reference content** (videos that have been pre-processed into the FAISS vector database). Google Web Detection will be the future real-world engine, but it is not a dedicated movie-recognition database.

## Metadata Enrichment
TMDb enrichment is optional and strictly separate from recognition. It does not identify a movie from screenshots; it only pulls canonical details (year, overview, poster) for an already recognized title if `TMDB_BEARER_TOKEN` is present in the backend environment.

## Privacy & Ephemerality
The backend deletes all uploaded temporary JPEG and WAV files immediately after processing. No frames or audio are persisted, and there is no database storing user queries.
