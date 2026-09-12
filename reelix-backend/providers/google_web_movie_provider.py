from typing import List
import config
from providers.base_movie_provider import BaseMovieProvider
from models.recognition_result import MovieRecognitionResult

class GoogleWebMovieProvider(BaseMovieProvider):
    @property
    def provider_name(self) -> str:
        return "google_web_movie"
        
    def is_enabled(self) -> bool:
        return config.GOOGLE_WEB_DETECTION_ENABLED
        
    def recognize(self, frame_paths: List[str]) -> MovieRecognitionResult:
        if not self.is_enabled():
            print(f"[EXTERNAL_MOVIE] skipped reason=disabled_by_config")
            return MovieRecognitionResult(state="SKIPPED", provider=self.provider_name)
            
        # For now, even if enabled, we don't have credentials in this task.
        print(f"[EXTERNAL_MOVIE] skipped reason=disabled_no_credentials")
        return MovieRecognitionResult(state="SKIPPED", provider=self.provider_name)
