from typing import List, Optional, Dict, Any
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
        
    def get_health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "providers": {
                "local_movie": "ready" if self.local_movie._is_ready else "not_ready",
                "local_music": "ready" if self.local_music._is_ready else "not_ready",
                "google_web_movie": "ready" if self.external_movie.is_enabled() else "disabled_by_config",
                "audd_music": "ready" if self.external_music.is_enabled() else "disabled_by_config",
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
            
            if ext_result.state != "SKIPPED":
                # Assuming ocr_evidence might be fetched or used later
                candidates = self.candidate_extractor.extract(ext_result, "")
                if candidates:
                    # In a real scenario, this resolves to a canonical title
                    resolved_meta = self.metadata_service.resolve_candidate(candidates[0].title)
                    if resolved_meta:
                        ext_result.metadata = resolved_meta
                        ext_result.title = resolved_meta.get("canonical_title", candidates[0].title)
                        ext_result.state = "MATCH"
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
            if ext_result.state != "SKIPPED":
                result = ext_result
            else:
                result = local_result
                
        if not result or result.state == "SKIPPED":
            return {
                "state": "UNAVAILABLE",
                "track": None,
                "score": 0.0,
                "provider": "none"
            }
            
        return {
            "state": result.state,
            "track": result.track,
            "score": result.score,
            "provider": result.provider
        }
