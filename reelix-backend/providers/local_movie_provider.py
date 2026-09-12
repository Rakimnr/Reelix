import sys
import os
import numpy as np
from typing import List

# Ensure we can import from recognition-spike
sys.path.append(os.path.abspath("../recognition-spike"))
from src.embedding_service import EmbeddingService
from src.index_builder import IndexBuilder
from src.query_matcher import QueryMatcher
from src.ocr_service import OCRService

from providers.base_movie_provider import BaseMovieProvider
from models.recognition_result import MovieRecognitionResult

class LocalMovieProvider(BaseMovieProvider):
    def __init__(self):
        self._embedder = None
        self._ocr_service = None
        self._visual_index = None
        self._visual_matcher = None
        self._is_ready = False
        
    @property
    def provider_name(self) -> str:
        return "local_index"
        
    def is_enabled(self) -> bool:
        return True
        
    def initialize(self):
        if self._is_ready:
            return
            
        print(f"[Backend] Loading {self.provider_name} OpenCLIP ViT-B-32...")
        self._embedder = EmbeddingService()
        
        print(f"[Backend] Loading {self.provider_name} OCR Service...")
        self._ocr_service = OCRService()
        
        print(f"[Backend] Loading {self.provider_name} FAISS Visual Index...")
        self._visual_index = IndexBuilder()
        self._visual_index.load(
            os.path.join("../recognition-spike/index", "visual.index"),
            os.path.join("../recognition-spike/index", "metadata.json")
        )
        self._visual_matcher = QueryMatcher(self._visual_index)
        self._is_ready = True
        print(f"[Backend] {self.provider_name} ready")
        
    def recognize(self, frame_paths: List[str]) -> MovieRecognitionResult:
        if not self._is_ready:
            return MovieRecognitionResult(state="ERROR", provider=self.provider_name)
            
        try:
            query_embeddings = []
            query_ocr_texts = []
            
            for frame_path in frame_paths:
                emb = self._embedder.get_embedding(frame_path)
                query_embeddings.append(emb)
                
                _, clean_text = self._ocr_service.extract_text(frame_path)
                query_ocr_texts.append(clean_text)
                
            if query_embeddings:
                query_matrix = np.vstack(query_embeddings)
                diagnostics, results = self._visual_matcher.search(
                    query_matrix,
                    query_ocr_texts=query_ocr_texts,
                    top_k=5,
                    match_threshold=0.85,
                    possible_threshold=0.75
                )
                
                decision = diagnostics["decision"]
                best_title = diagnostics["best_title"] if decision != "NO_MATCH" else None
                visual_score = float(diagnostics["best_score"])
                ocr_score = float(diagnostics["ocr_similarity"])
                
                if decision != "NO_MATCH" and diagnostics.get("ocr_best_title") and best_title != diagnostics.get("ocr_best_title"):
                    best_title = diagnostics["ocr_best_title"] if decision == "POSSIBLE_MATCH" else best_title
                    
                return MovieRecognitionResult(
                    state=decision,
                    title=best_title,
                    visual_score=visual_score,
                    ocr_score=ocr_score,
                    provider=self.provider_name
                )
            else:
                return MovieRecognitionResult(state="NO_MATCH", provider=self.provider_name)
                
        except Exception as e:
            print(f"[{self.provider_name}] Error: {e}")
            return MovieRecognitionResult(state="VISUAL_ERROR", provider=self.provider_name)
