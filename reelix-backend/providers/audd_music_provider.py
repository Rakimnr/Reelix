from typing import Optional
import time
import requests
import config
from providers.base_music_provider import BaseMusicProvider
from models.recognition_result import MusicRecognitionResult

class AudDMusicProvider(BaseMusicProvider):
    @property
    def provider_name(self) -> str:
        return "audd_music"
        
    def is_enabled(self) -> bool:
        return config.AUDD_ENABLED
        
    def recognize(self, audio_path: Optional[str]) -> MusicRecognitionResult:
        start_time = time.time()
        print(f"[EXTERNAL_MUSIC] provider=audd started")
        
        if not self.is_enabled():
            print(f"[EXTERNAL_MUSIC] skipped reason=disabled_by_config")
            return MusicRecognitionResult(state="SKIPPED", provider=self.provider_name)
            
        if not config.AUDD_API_TOKEN:
            print(f"[EXTERNAL_MUSIC] skipped reason=disabled_no_credentials")
            return MusicRecognitionResult(state="SKIPPED", provider=self.provider_name)
            
        if not audio_path:
            return MusicRecognitionResult(state="ERROR", provider=self.provider_name)
            
        try:
            url = "https://api.audd.io/"
            data = {
                "api_token": config.AUDD_API_TOKEN,
                "return": "apple_music,spotify"
            }
            with open(audio_path, "rb") as f:
                files = {"file": f}
                resp = requests.post(url, data=data, files=files, timeout=config.EXTERNAL_PROVIDER_TIMEOUT_SECONDS)
                
            resp.raise_for_status()
            res_json = resp.json()
            
            if res_json.get("status") == "success" and res_json.get("result"):
                r = res_json["result"]
                res = MusicRecognitionResult(
                    state="MATCH",
                    track=r.get("title"),
                    artist=r.get("artist"),
                    album=r.get("album"),
                    release_date=r.get("release_date"),
                    song_link=r.get("song_link"),
                    provider=self.provider_name
                )
            elif res_json.get("status") == "error":
                err_msg = res_json.get("error", {}).get("error_message", "Unknown AudD error")
                err_code = res_json.get("error", {}).get("error_code", 0)
                print(f"[EXTERNAL_MUSIC] API Error {err_code}: {err_msg}")
                res = MusicRecognitionResult(state="ERROR", provider=self.provider_name)
            else:
                res = MusicRecognitionResult(state="NO_MATCH", provider=self.provider_name)
                
            elapsed = int((time.time() - start_time) * 1000)
            print(f"[EXTERNAL_MUSIC] state={res.state} elapsed_ms={elapsed}")
            return res
            
        except requests.exceptions.Timeout:
            print(f"[EXTERNAL_MUSIC] error=timeout elapsed_ms={int((time.time() - start_time)*1000)}")
            return MusicRecognitionResult(state="ERROR", provider=self.provider_name)
        except Exception as e:
            print(f"[EXTERNAL_MUSIC] error={type(e).__name__} elapsed_ms={int((time.time() - start_time)*1000)}")
            return MusicRecognitionResult(state="ERROR", provider=self.provider_name)
