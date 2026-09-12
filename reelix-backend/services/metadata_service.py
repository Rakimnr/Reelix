import os
import requests
from typing import Dict, Any, Optional

class MetadataService:
    def __init__(self):
        self.token = os.environ.get("TMDB_BEARER_TOKEN")
        
    def is_enabled(self) -> bool:
        return bool(self.token)
        
    def resolve_candidate(self, title: str) -> Optional[Dict[str, Any]]:
        if not self.is_enabled() or not title:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json"
            }
            url = f"https://api.themoviedb.org/3/search/multi?query={requests.utils.quote(title)}&include_adult=false&language=en-US&page=1"
            
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("results"):
                    best = data["results"][0]
                    return {
                        "tmdb_id": best.get("id"),
                        "canonical_title": best.get("title") or best.get("name"),
                        "media_type": best.get("media_type"),
                        "release_date": best.get("release_date") or best.get("first_air_date"),
                        "overview": best.get("overview"),
                        "poster_path": best.get("poster_path")
                    }
            return None
        except Exception as e:
            print(f"[MetadataService] Error: {e}")
            return None
            
    def enrich_movie(self, title: str) -> Optional[Dict[str, Any]]:
        return self.resolve_candidate(title)
