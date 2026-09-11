import os
import sys
import time
import shutil
import numpy as np
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, BackgroundTasks

sys.path.append(os.path.abspath("../recognition-spike"))
sys.path.append(os.path.abspath("../music-spike"))

from src.embedding_service import EmbeddingService
from src.index_builder import IndexBuilder
from src.query_matcher import QueryMatcher
from src.ocr_service import OCRService
from src.fingerprint_service import FingerprintService
from src.catalogue_builder import CatalogueBuilder
from src.music_matcher import MusicMatcher
from src.audio_extractor import AudioExtractor

app = FastAPI()

# Global initializations
embedder = None
ocr_service = None
visual_index = None
visual_matcher = None

fingerprinter = None
music_catalogue = None
music_matcher = None
audio_extractor = None

def init_services():
    global embedder, ocr_service, visual_index, visual_matcher
    global fingerprinter, music_catalogue, music_matcher, audio_extractor

    if embedder is None:
        embedder = EmbeddingService()
        ocr_service = OCRService()
        visual_index = IndexBuilder()
        visual_index.load(
            os.path.join("../recognition-spike/index", "visual.index"),
            os.path.join("../recognition-spike/index", "metadata.json")
        )
        visual_matcher = QueryMatcher(visual_index)

        fingerprinter = FingerprintService()
        music_catalogue = CatalogueBuilder("../music-spike/index/catalogue.db")
        music_matcher = MusicMatcher(music_catalogue)
        audio_extractor = AudioExtractor()

@app.on_event("startup")
def startup_event():
    init_services()

@app.post("/recognize")
async def recognize(
    frames: List[UploadFile] = File(...),
    audio: Optional[UploadFile] = File(None)
):
    start_time = time.time()
    
    os.makedirs("temp", exist_ok=True)
    temp_files = []
    
    # 1. VISUAL PIPELINE
    visual_start = time.time()
    movie_result = {
        "state": "NO_MATCH",
        "title": None,
        "visual_score": 0.0,
        "ocr_score": 0.0
    }
    
    try:
        query_embeddings = []
        query_ocr_texts = []
        
        for frame in frames:
            frame_path = os.path.join("temp", frame.filename)
            with open(frame_path, "wb") as f:
                shutil.copyfileobj(frame.file, f)
            temp_files.append(frame_path)
            
            emb = embedder.get_embedding(frame_path)
            query_embeddings.append(emb)
            
            _, clean_text = ocr_service.extract_text(frame_path)
            query_ocr_texts.append(clean_text)
            
        if query_embeddings:
            query_matrix = np.vstack(query_embeddings)
            diagnostics, results = visual_matcher.search(
                query_matrix,
                query_ocr_texts=query_ocr_texts,
                top_k=5,
                match_threshold=0.85,
                possible_threshold=0.75
            )
            movie_result["state"] = diagnostics["decision"]
            movie_result["title"] = diagnostics["best_title"] if diagnostics["decision"] != "NO_MATCH" else None
            movie_result["visual_score"] = float(diagnostics["best_score"])
            movie_result["ocr_score"] = float(diagnostics["ocr_similarity"])
            if diagnostics["decision"] != "NO_MATCH" and diagnostics["ocr_best_title"] and movie_result["title"] != diagnostics["ocr_best_title"]:
                 movie_result["title"] = diagnostics["ocr_best_title"] if diagnostics["decision"] == "POSSIBLE_MATCH" else movie_result["title"]

    except Exception as e:
        print(f"Visual Error: {e}")
        movie_result["state"] = "VISUAL_ERROR"
        
    visual_ms = int((time.time() - visual_start) * 1000)
    
    # 2. AUDIO PIPELINE
    music_start = time.time()
    music_result = {
        "state": "UNAVAILABLE",
        "track": None,
        "score": 0
    }
    
    if audio:
        try:
            audio_path = os.path.join("temp", audio.filename)
            with open(audio_path, "wb") as f:
                shutil.copyfileobj(audio.file, f)
            temp_files.append(audio_path)
            
            # Use extractor to read the WAV
            sr, audio_data = audio_extractor.load_audio(audio_path)
            hashes = fingerprinter.generate_fingerprints(audio_data, sr)
            decision, best_track_id, best_score, second_best_score, margin, best_offset = music_matcher.match(hashes)
            
            music_result["state"] = decision
            if decision != "NO_MATCH":
                music_result["track"] = best_track_id
            music_result["score"] = best_score
        except Exception as e:
            print(f"Audio Error: {e}")
            music_result["state"] = "AUDIO_ERROR"
            
    music_ms = int((time.time() - music_start) * 1000)
    
    # Cleanup temp
    for f in temp_files:
        try:
            os.remove(f)
        except:
            pass
            
    total_ms = int((time.time() - start_time) * 1000)
    
    return {
        "movie": movie_result,
        "music": music_result,
        "timing_ms": {
            "visual": visual_ms,
            "ocr": 0, # integrated in visual loop for now
            "music": music_ms,
            "total": total_ms
        }
    }

if __name__ == "__main__":
    import uvicorn
    # Make accessible on local network via 0.0.0.0
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
