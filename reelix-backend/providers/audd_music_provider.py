from typing import Optional
import os
import config
from providers.base_music_provider import BaseMusicProvider
from models.recognition_result import MusicRecognitionResult

class AudDMusicProvider(BaseMusicProvider):
    def __init__(self):
        self.api_token = os.environ.get("AUDD_API_TOKEN")
        
    @property
    def provider_name(self) -> str:
        return "audd_music"
        
    def is_enabled(self) -> bool:
        return config.AUDD_ENABLED and bool(self.api_token)
        
    def recognize(self, audio_path: Optional[str]) -> MusicRecognitionResult:
        if not config.AUDD_ENABLED:
            print(f"[EXTERNAL_MUSIC] skipped reason=disabled_by_config")
            return MusicRecognitionResult(state="SKIPPED", provider=self.provider_name)
            
        if not self.api_token:
            print(f"[EXTERNAL_MUSIC] skipped reason=disabled_no_credentials")
            return MusicRecognitionResult(state="SKIPPED", provider=self.provider_name)
            
        return MusicRecognitionResult(state="SKIPPED", provider=self.provider_name)
