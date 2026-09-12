from abc import ABC, abstractmethod
from typing import Optional
from models.recognition_result import MusicRecognitionResult

class BaseMusicProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
        
    @abstractmethod
    def is_enabled(self) -> bool:
        pass
        
    @abstractmethod
    def recognize(self, audio_path: Optional[str]) -> MusicRecognitionResult:
        pass
