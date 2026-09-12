from typing import List
from providers.base_movie_provider import BaseMovieProvider
from models.recognition_result import MovieRecognitionResult

class ExternalMovieProvider(BaseMovieProvider):
    @property
    def provider_name(self) -> str:
        return "external_movie"
        
    def is_enabled(self) -> bool:
        return False
        
    def recognize(self, frame_paths: List[str]) -> MovieRecognitionResult:
        return MovieRecognitionResult(state="SKIPPED", provider=self.provider_name)
