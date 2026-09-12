import os
import time
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File

from services.recognition_orchestrator import RecognitionOrchestrator

app = FastAPI()
orchestrator = RecognitionOrchestrator()

@app.on_event("startup")
def startup_event():
    orchestrator.initialize()

@app.get("/health")
def health_check():
    return orchestrator.get_health()

@app.post("/recognize")
async def recognize(
    frames: List[UploadFile] = File(...),
    audio: Optional[UploadFile] = File(None)
):
    start_time = time.time()
    
    os.makedirs("temp", exist_ok=True)
    temp_files = []
    
    # 1. SETUP EVIDENCE
    frame_paths = []
    for frame in frames:
        frame_path = os.path.join("temp", frame.filename)
        with open(frame_path, "wb") as f:
            shutil.copyfileobj(frame.file, f)
        temp_files.append(frame_path)
        frame_paths.append(frame_path)
        
    audio_path = None
    if audio:
        audio_path = os.path.join("temp", audio.filename)
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        temp_files.append(audio_path)
    
    # 2. VISUAL PIPELINE
    visual_start = time.time()
    movie_result = orchestrator.recognize_movie(frame_paths)
    visual_ms = int((time.time() - visual_start) * 1000)
    
    # 3. AUDIO PIPELINE
    music_start = time.time()
    music_result = orchestrator.recognize_music(audio_path)
    music_ms = int((time.time() - music_start) * 1000)
    
    # 4. CLEANUP TEMP
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
