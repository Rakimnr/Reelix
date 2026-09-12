import os
import requests
from typing import Dict, Any, Optional, List
import config

class MetadataService:
    def __init__(self):
        self.token = config.TMDB_BEARER_TOKEN
        
    def is_enabled(self) -> bool:
        return bool(self.token)
        
    def resolve_candidates(self, candidates: List[str]) -> Optional[Dict[str, Any]]:
        if not self.is_enabled() or not candidates:
            return None
            
        headers = {
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json"
        }
        
        # Limit to top 3 candidates to save API calls
        for title in candidates[:3]:
            try:
                url = f"https://api.themoviedb.org/3/search/multi?query={requests.utils.quote(title)}&include_adult=false&language=en-US&page=1"
                resp = requests.get(url, headers=headers, timeout=config.EXTERNAL_PROVIDER_TIMEOUT_SECONDS)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("results"):
                        # Just take the first valid result from TMDb for this candidate
                        best = data["results"][0]
                        return {
                            "tmdb_id": best.get("id"),
                            "canonical_title": best.get("title") or best.get("name"),
                            "media_type": best.get("media_type"),
                            "release_date": best.get("release_date") or best.get("first_air_date"),
                            "overview": best.get("overview"),
                            "poster_path": best.get("poster_path")
                        }
            except Exception as e:
                print(f"[MetadataService] Error resolving '{title}': {type(e).__name__}")
                continue
                
        return None
        
    def resolve_candidate(self, title: str) -> Optional[Dict[str, Any]]:
        return self.resolve_candidates([title])
            
    def enrich_movie(self, title: str) -> Optional[Dict[str, Any]]:
        return self.resolve_candidate(title)
