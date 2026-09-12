from typing import List
from models.recognition_result import MovieRecognitionResult, CandidateTitle

class MovieCandidateExtractor:
    STOP_WORDS = {"film", "movie", "scene", "edit", "tiktok", "instagram", "youtube", "video", "clip", "full"}

    def extract(self, result: MovieRecognitionResult, ocr_text: str = "") -> List[CandidateTitle]:
        candidates_map = {}

        def add_candidate(raw_title: str, source: str, weight: int = 1):
            if not raw_title:
                return
                
            title = raw_title.lower().strip()
            
            # Trim noise / Stop words check
            for sw in self.STOP_WORDS:
                title = title.replace(sw, "").strip()
                
            # If after trim it's empty or too short, discard
            if len(title) < 2:
                return
                
            if title not in candidates_map:
                candidates_map[title] = {"score": 0, "sources": set()}
                
            candidates_map[title]["score"] += weight
            candidates_map[title]["sources"].add(source)

        # 1. Web Entities
        for entity in result.web_entities:
            add_candidate(entity, "web_entity", weight=2)
            
        # 2. Page Titles (often contain "Movie Title (2023) - IMDb" etc, keeping it simple)
        for page_title in result.matching_page_titles:
            # simple split by common separators
            parts = page_title.split("-")
            add_candidate(parts[0], "page_title", weight=1)
            
        # 3. Best Guess Labels
        for label in result.best_guess_labels:
            add_candidate(label, "best_guess", weight=3)
            
        # 4. OCR text
        if ocr_text:
            # OCR is usually raw, maybe just use lines
            for line in ocr_text.split('\n'):
                add_candidate(line, "ocr", weight=1)
                
        # Combine and sort
        final_candidates = []
        for t, data in candidates_map.items():
            final_candidates.append(CandidateTitle(
                title=t.title(), # Title case for normalization
                score=data["score"],
                sources=list(data["sources"])
            ))
            
        final_candidates.sort(key=lambda x: x.score, reverse=True)
        return final_candidates
