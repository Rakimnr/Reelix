import os
import argparse
import time
import json
from src.audio_extractor import AudioExtractor
from src.fingerprint_service import FingerprintService
from src.catalogue_builder import CatalogueBuilder
from src.music_matcher import MusicMatcher
from src.audio_simulator import AudioSimulator

def main():
    parser = argparse.ArgumentParser(description="Query the Music Index.")
    parser.add_argument("query_audio", help="Path to the query clip")
    parser.add_argument("--expected-state", default="KNOWN", choices=["KNOWN", "UNKNOWN"])
    parser.add_argument("--expected-track", default="")
    parser.add_argument("--degradation", default="CLEAN", choices=["CLEAN", "LIGHT", "MEDIUM", "HEAVY", "VOICE_OVER", "SPEED_UP", "SLOW_DOWN", "REVERB"])
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--start-pos", type=float, default=0.0)
    parser.add_argument("--db-path", default="index/catalogue.db")
    
    args = parser.parse_args()
    
    extractor = AudioExtractor()
    fingerprinter = FingerprintService()
    catalogue = CatalogueBuilder(args.db_path)
    matcher = MusicMatcher(catalogue)
    simulator = AudioSimulator()
    
    os.makedirs("results", exist_ok=True)
    temp_dir = "extracted/queries"
    os.makedirs(temp_dir, exist_ok=True)
    
    start_time = time.time()
    
    try:
        # 1. Extract/Format Audio
        print(f"1. Preparing audio ({args.query_audio})...")
        base_name = os.path.basename(args.query_audio)
        out_wav = os.path.join(temp_dir, f"raw_{base_name}.wav")
        extractor.extract_audio(args.query_audio, out_wav)
        sr, audio_data = extractor.load_audio(out_wav)
        
        # 2. Extract Segment
        print(f"2. Extracting {args.duration}s segment at {args.start_pos}s...")
        segment = simulator.extract_segment(audio_data, args.duration, args.start_pos)
        
        # 3. Degrade
        print(f"3. Applying {args.degradation} degradation...")
        degraded = simulator.degrade(segment, args.degradation)
        
        # 4. Fingerprint
        print("4. Generating query hashes...")
        hashes = fingerprinter.generate_fingerprints(degraded, sr)
        
        # 5. Search
        print(f"5. Searching catalogue (Query Hashes: {len(hashes)})...")
        decision, best_track_id, best_score, second_best_score, margin, best_offset = matcher.match(hashes)
        
        proc_time = time.time() - start_time
        
        # Evaluate
        if args.expected_state == "KNOWN":
            correct_decision = (decision in ["MATCH", "POSSIBLE_MATCH"]) and (args.expected_track == best_track_id)
        else:
            correct_decision = (decision == "NO_MATCH")
            
        record = {
            "query": base_name,
            "expected_state": args.expected_state,
            "expected_track": args.expected_track,
            "sample_duration": args.duration,
            "sample_start_position": args.start_pos,
            "degradation": args.degradation,
            "predicted_track": best_track_id,
            "best_score": best_score,
            "second_best_score": second_best_score,
            "margin": margin,
            "decision": decision,
            "correct_decision": correct_decision,
            "processing_time": round(proc_time, 2)
        }
        
        res_file = os.path.join("results", f"eval_{args.degradation}_{args.duration}s_{args.start_pos:.1f}s_{base_name}.json")
        with open(res_file, 'w') as f:
            json.dump(record, f, indent=2)
            
        print("\n--- Audio Fingerprint Results ---")
        print(f"Decision: {decision} (Expected: {args.expected_state})")
        print(f"Correct Decision: {correct_decision}")
        print(f"Predicted Track: {best_track_id}")
        print(f"Best Score: {best_score} matching hashes")
        print(f"Processing time: {record['processing_time']}s")
        print(f"Saved to: {res_file}\n")
        
    finally:
        if 'out_wav' in locals() and os.path.exists(out_wav):
            os.remove(out_wav)

if __name__ == "__main__":
    main()
