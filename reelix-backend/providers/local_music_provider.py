import sys
import os
from typing import Optional

sys.path.append(os.path.abspath("../music-spike"))
from src.fingerprint_service import FingerprintService
from src.catalogue_builder import CatalogueBuilder
from src.music_matcher import MusicMatcher
from src.audio_extractor import AudioExtractor

from providers.base_music_provider import BaseMusicProvider
from models.recognition_result import MusicRecognitionResult

class LocalMusicProvider(BaseMusicProvider):
    def __init__(self):
        self._fingerprinter = None
        self._music_catalogue = None
        self._music_matcher = None
        self._audio_extractor = None
        self._is_ready = False
        
    @property
    def provider_name(self) -> str:
        return "local_fingerprint"
        
    def is_enabled(self) -> bool:
        return True
        
    def initialize(self):
        if self._is_ready:
            return
            
        print(f"[Backend] Loading {self.provider_name} Catalogue...")
        self._fingerprinter = FingerprintService()
        self._music_catalogue = CatalogueBuilder("../music-spike/index/catalogue.db")
        self._music_matcher = MusicMatcher(self._music_catalogue)
        self._audio_extractor = AudioExtractor()
        
        self._is_ready = True
        print(f"[Backend] {self.provider_name} ready")
        
    def recognize(self, audio_path: Optional[str]) -> MusicRecognitionResult:
        if not self._is_ready:
            return MusicRecognitionResult(state="ERROR", provider=self.provider_name)
            
        if not audio_path:
            return MusicRecognitionResult(state="UNAVAILABLE", provider=self.provider_name)
            
        try:
            sr, audio_data = self._audio_extractor.load_audio(audio_path)
            hashes = self._fingerprinter.generate_fingerprints(audio_data, sr)
            decision, best_track_id, best_score, second_best_score, margin, best_offset = self._music_matcher.match(hashes)
            
            return MusicRecognitionResult(
                state=decision,
                track=best_track_id if decision != "NO_MATCH" else None,
                score=best_score,
                provider=self.provider_name
            )
        except Exception as e:
            print(f"[{self.provider_name}] Error: {e}")
            return MusicRecognitionResult(state="AUDIO_ERROR", provider=self.provider_name)
