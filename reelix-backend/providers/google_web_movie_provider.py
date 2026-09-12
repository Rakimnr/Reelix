import base64
import time
import requests
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
        start_time = time.time()
        print(f"[EXTERNAL_MOVIE] provider=google_web started")
        
        if not self.is_enabled():
            print(f"[EXTERNAL_MOVIE] skipped reason=disabled_by_config")
            return MovieRecognitionResult(state="SKIPPED", provider=self.provider_name)
            
        if not config.GOOGLE_API_KEY:
            print(f"[EXTERNAL_MOVIE] skipped reason=disabled_no_credentials")
            return MovieRecognitionResult(state="SKIPPED", provider=self.provider_name)
            
        if not frame_paths:
            return MovieRecognitionResult(state="ERROR", provider=self.provider_name)
            
        selected_frame = frame_paths[0]
        print(f"[EXTERNAL_MOVIE] selected_frame={selected_frame}")
        
        try:
            with open(selected_frame, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
                
            payload = {
                "requests": [{
                    "image": {"content": img_b64},
                    "features": [{"type": "WEB_DETECTION"}]
                }]
            }
            
            url = f"https://vision.googleapis.com/v1/images:annotate?key={config.GOOGLE_API_KEY}"
            resp = requests.post(url, json=payload, timeout=config.EXTERNAL_PROVIDER_TIMEOUT_SECONDS)
            resp.raise_for_status()
            
            data = resp.json()
            responses = data.get("responses", [])
            if not responses:
                return MovieRecognitionResult(state="NO_MATCH", provider=self.provider_name)
                
            web_det = responses[0].get("webDetection", {})
            
            res = MovieRecognitionResult(
                state="POSSIBLE",
                provider=self.provider_name,
                best_guess_labels=[l.get("label") for l in web_det.get("bestGuessLabels", []) if "label" in l],
                web_entities=[e.get("description") for e in web_det.get("webEntities", []) if "description" in e],
                matching_page_titles=[p.get("pageTitle") for p in web_det.get("pagesWithMatchingImages", []) if "pageTitle" in p],
                matching_page_urls=[p.get("url") for p in web_det.get("pagesWithMatchingImages", []) if "url" in p],
                full_match_count=len(web_det.get("fullMatchingImages", [])),
                partial_match_count=len(web_det.get("partialMatchingImages", [])),
                provider_score=0.0
            )
            
            elapsed = int((time.time() - start_time) * 1000)
            print(f"[EXTERNAL_MOVIE] state={res.state} elapsed_ms={elapsed}")
            return res
            
        except requests.exceptions.Timeout:
            print(f"[EXTERNAL_MOVIE] error=timeout elapsed_ms={int((time.time() - start_time)*1000)}")
            return MovieRecognitionResult(state="ERROR", provider=self.provider_name)
        except Exception as e:
            print(f"[EXTERNAL_MOVIE] error={type(e).__name__} elapsed_ms={int((time.time() - start_time)*1000)}")
            return MovieRecognitionResult(state="ERROR", provider=self.provider_name)
