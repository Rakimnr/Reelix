from typing import Optional
from providers.base_music_provider import BaseMusicProvider
from models.recognition_result import MusicRecognitionResult

class ExternalMusicProvider(BaseMusicProvider):
    @property
    def provider_name(self) -> str:
        return "external_music"
        
    def is_enabled(self) -> bool:
        return False
        
    def recognize(self, audio_path: Optional[str]) -> MusicRecognitionResult:
        return MusicRecognitionResult(state="SKIPPED", provider=self.provider_name)
