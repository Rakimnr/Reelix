from typing import List, Optional, Dict, Any
import config
from providers.local_movie_provider import LocalMovieProvider
from providers.google_web_movie_provider import GoogleWebMovieProvider
from providers.local_music_provider import LocalMusicProvider
from providers.audd_music_provider import AudDMusicProvider
from services.metadata_service import MetadataService
from services.fusion_service import FusionService
from services.frame_selector import FrameSelector
from services.candidate_extractor import MovieCandidateExtractor

class RecognitionOrchestrator:
    def __init__(self):
        self.local_movie = LocalMovieProvider()
        self.external_movie = GoogleWebMovieProvider()
        
        self.local_music = LocalMusicProvider()
        self.external_music = AudDMusicProvider()
        
        self.metadata_service = MetadataService()
        self.fusion_service = FusionService()
        self.frame_selector = FrameSelector()
        self.candidate_extractor = MovieCandidateExtractor()
        
    def initialize(self):
        self.local_movie.initialize()
        self.local_music.initialize()
        
    def _get_provider_health(self, enabled: bool, has_creds: bool) -> str:
        if not enabled:
            return "disabled_by_config"
        if not has_creds:
            return "error_missing_credentials"
        return "ready"
        
    def get_health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "providers": {
                "local_movie": "ready" if self.local_movie._is_ready else "not_ready",
                "local_music": "ready" if self.local_music._is_ready else "not_ready",
                "google_web_movie": self._get_provider_health(config.GOOGLE_WEB_DETECTION_ENABLED, bool(config.GOOGLE_API_KEY)),
                "audd_music": self._get_provider_health(config.AUDD_ENABLED, bool(config.AUDD_API_TOKEN)),
                "tmdb_metadata": "enabled" if self.metadata_service.is_enabled() else "disabled_no_token"
            }
        }
        
    def recognize_movie(self, frame_paths: List[str]) -> Dict[str, Any]:
        # Always run local
        local_result = self.local_movie.recognize(frame_paths)
        
        results = [local_result]
        
        # If local didn't get a strong match, try external
        if local_result.state not in ["MATCH"]:
            best_frame, score, reason = self.frame_selector.select_best_frame(frame_paths)
            ext_result = self.external_movie.recognize([best_frame])
            
            if ext_result.state not in ["SKIPPED", "ERROR"]:
                # Assuming local_result might have some OCR evidence
                candidates = self.candidate_extractor.extract(ext_result, "")
                print(f"[EXTERNAL_MOVIE] candidates={len(candidates)}")
                
                if candidates:
                    candidate_titles = [c.title for c in candidates]
                    resolved_meta = self.metadata_service.resolve_candidates(candidate_titles)
                    
                    if resolved_meta:
                        ext_result.metadata = resolved_meta
                        ext_result.title = resolved_meta.get("canonical_title", candidate_titles[0])
                        
                        # Decision logic
                        best_candidate = next((c for c in candidates if c.title.lower() == ext_result.title.lower()), candidates[0])
                        
                        if len(best_candidate.sources) > 1:
                            ext_result.state = "MATCH"
                        else:
                            ext_result.state = "POSSIBLE"
                    else:
                        ext_result.title = candidate_titles[0]
                        ext_result.state = "POSSIBLE"
                else:
                    ext_result.state = "NO_MATCH"
                
                results.append(ext_result)
            
        fused = self.fusion_service.fuse_movie_results(results)
        
        # Enrich if MATCH or POSSIBLE (Local might need enrichment)
        if fused.state in ["MATCH", "POSSIBLE"] and fused.title and not fused.metadata:
            fused.metadata = self.metadata_service.enrich_movie(fused.title)
            
        return {
            "state": fused.state,
            "title": fused.title,
            "visual_score": fused.visual_score,
            "ocr_score": fused.ocr_score,
            "provider": fused.provider,
            "metadata": fused.metadata
        }
        
    def recognize_music(self, audio_path: Optional[str]) -> Dict[str, Any]:
        local_result = None
        if self.local_music.is_enabled():
            local_result = self.local_music.recognize(audio_path)
            
        if local_result and local_result.state == "MATCH":
            result = local_result
        else:
            ext_result = self.external_music.recognize(audio_path)
            if ext_result.state not in ["SKIPPED", "ERROR"]:
                result = ext_result
            else:
                result = local_result
                
        if not result or result.state in ["SKIPPED", "ERROR"]:
            return {
                "state": "UNAVAILABLE",
                "track": None,
                "score": 0.0,
                "provider": "none"
            }
            
        # For external fields
        return_data = {
            "state": result.state,
            "track": result.track,
            "score": result.score,
            "provider": result.provider
        }
        
        if result.provider == "audd_music":
            return_data.update({
                "artist": getattr(result, "artist", None),
                "album": getattr(result, "album", None),
                "release_date": getattr(result, "release_date", None),
                "song_link": getattr(result, "song_link", None)
            })
            
        return return_data
