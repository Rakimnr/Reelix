import os
import argparse
from src.audio_extractor import AudioExtractor
from src.fingerprint_service import FingerprintService
from src.catalogue_builder import CatalogueBuilder

def main():
    parser = argparse.ArgumentParser(description="Build Audio Fingerprint Catalogue.")
    parser.add_argument("--ref-dir", default="../recognition-spike/references", help="Directory containing reference video/audio files")
    parser.add_argument("--db-path", default="index/catalogue.db", help="Path to save SQLite database")
    
    args = parser.parse_args()
    
    extractor = AudioExtractor()
    fingerprinter = FingerprintService()
    catalogue = CatalogueBuilder(args.db_path)
    catalogue.init_db()
    
    os.makedirs(args.ref_dir, exist_ok=True)
    temp_dir = "extracted/references"
    os.makedirs(temp_dir, exist_ok=True)
    
    import json
    
    metadata_file = os.path.join(args.ref_dir, "reference_metadata.json")
    metadata_map = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            metadata_map = json.load(f)
            
    processed = 0
    for filename in os.listdir(args.ref_dir):
        if not filename.endswith((".mp3", ".wav", ".m4a", ".mp4")):
            continue
            
        input_path = os.path.join(args.ref_dir, filename)
        track_id = os.path.splitext(filename)[0]
        
        # Merge with JSON metadata if present
        track_meta = metadata_map.get(filename, metadata_map.get(track_id, {}))
        # Label is the source video name for this clip-matching experiment
        title = track_meta.get("title", track_id)
        
        print(f"Processing reference: {title}")
        
        # 1. Extract/Format Audio
        out_wav = os.path.join(temp_dir, f"{track_id}.wav")
        try:
            extractor.extract_audio(input_path, out_wav)
        except Exception as e:
            print(f"Skipping {filename}: {e}")
            continue
            
        # 2. Load and Fingerprint
        sr, audio_data = extractor.load_audio(out_wav)
        duration = len(audio_data) / sr
        
        hashes = fingerprinter.generate_fingerprints(audio_data, sr)
        print(f"  Generated {len(hashes)} hashes.")
        
        # 3. Store in DB
        catalogue.add_track(track_id, title, duration, hashes)
        processed += 1
        
        # 4. Cleanup temporary WAV
        if os.path.exists(out_wav):
            os.remove(out_wav)
        
    print(f"\nCatalogue built successfully with {processed} tracks.")

if __name__ == "__main__":
    main()
