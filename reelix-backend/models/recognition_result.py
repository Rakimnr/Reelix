from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class MovieRecognitionResult(BaseModel):
    state: str  # MATCH, POSSIBLE, NO_MATCH, ERROR, SKIPPED
    title: Optional[str] = None
    visual_score: float = 0.0
    ocr_score: float = 0.0
    provider: str
    external_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Optional fields for web detection
    best_guess_labels: List[str] = []
    web_entities: List[str] = []
    matching_page_titles: List[str] = []
    matching_page_urls: List[str] = []
    full_match_count: int = 0
    partial_match_count: int = 0
    candidate_titles: List[str] = []
    provider_score: float = 0.0

class MusicRecognitionResult(BaseModel):
    state: str  # MATCH, POSSIBLE, NO_MATCH, ERROR, SKIPPED, AUDIO_ERROR, UNAVAILABLE
    track: Optional[str] = None
    score: float = 0.0
    provider: str
    external_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Extended fields for AudD
    artist: Optional[str] = None
    album: Optional[str] = None
    release_date: Optional[str] = None
    song_link: Optional[str] = None

class CandidateTitle(BaseModel):
    title: str
    score: int
    sources: List[str] = []

