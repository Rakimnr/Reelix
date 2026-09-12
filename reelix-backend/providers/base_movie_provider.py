from abc import ABC, abstractmethod
from typing import List
from models.recognition_result import MovieRecognitionResult

class BaseMovieProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
        
    @abstractmethod
    def is_enabled(self) -> bool:
        pass
        
    @abstractmethod
    def recognize(self, frame_paths: List[str]) -> MovieRecognitionResult:
        pass
