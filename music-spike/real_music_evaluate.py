import os
import json
import csv
import sys
import subprocess
import glob
from collections import defaultdict
from src.audio_extractor import AudioExtractor

def calculate_accuracy(results, key, value):
    subset = [r for r in results if r.get(key) == value and r.get("expected_state") == "KNOWN"]
    if not subset:
        return 0.0
    correct = sum(1 for r in subset if r["correct_decision"])
    return (correct / len(subset)) * 100

def run_real_evaluation():
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Check what formats are supported based on FFmpeg
    extractor = AudioExtractor()
    has_ffmpeg = bool(extractor.ffmpeg_path)
    
    known_clips = []
    for ext in ["*.wav", "*.mp3", "*.m4a", "*.mp4"]:
        known_clips.extend(glob.glob(f"../recognition-spike/references/{ext}"))
        
    unknown_clips = []
    for ext in ["*.wav", "*.mp3", "*.m4a", "*.mp4"]:
        # Only taking the known unknown clips for the unknown queries
        unknown_clips.extend(glob.glob(f"../recognition-spike/queries/unknown/{ext}"))
        
    test_cases = []
    durations = [5.0, 8.0, 10.0]
    positions = [0.25, 0.50, 0.75] # 25%, 50%, 75%
    degradations = ["CLEAN", "LIGHT", "MEDIUM", "VOICE_OVER", "SPEED_UP", "SLOW_DOWN", "REVERB"]
    
    print("Parsing known reference files to create test cases...")
    for clip in known_clips:
        base = os.path.basename(clip)
        track = os.path.splitext(base)[0]
        
        # Determine actual length of the track
        try:
            temp_wav = os.path.join("extracted/queries", f"temp_{base}.wav")
            extractor.extract_audio(clip, temp_wav)
            sr, audio_data = extractor.load_audio(temp_wav)
            total_duration = len(audio_data) / sr
            os.remove(temp_wav)
        except Exception as e:
            print(f"Skipping {clip} for test generation: {e}")
            continue
            
        for dur in durations:
            for deg in degradations:
                for pos_pct in positions:
                    start_pos = total_duration * pos_pct
                    # Only add if the track is long enough
                    if start_pos + dur <= total_duration:
                        test_cases.append({
                            "file": clip, "state": "KNOWN", "track": track,
                            "degradation": deg, "duration": dur, "start": start_pos
                        })
                        
    print(f"Adding unknown clips...")
    for clip in unknown_clips:
        base = os.path.basename(clip)
        test_cases.append({
            "file": clip, "state": "UNKNOWN", "track": "",
            "degradation": "MEDIUM", "duration": 8.0, "start": 0.0
        })
        
    summary_data = []
    
    print(f"Running {len(test_cases)} total test cases...")
    for i, tc in enumerate(test_cases):
        base_name = os.path.basename(tc['file'])
        sys.stdout.write(f"\rProgress: {i+1}/{len(test_cases)} -> {base_name} [{tc['degradation']}, {tc['duration']}s, pos {tc['start']:.1f}s]      ")
        sys.stdout.flush()
        
        cmd = [
            sys.executable, "run_music_query.py", tc["file"],
            "--expected-state", tc["state"],
            "--expected-track", tc["track"],
            "--degradation", tc["degradation"],
            "--duration", str(tc["duration"]),
            "--start-pos", str(tc["start"])
        ]
        
        exec_status = "SUCCESS"
        error_msg = ""
        try:
            # Capture stdout and stderr
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            exec_status = "EXECUTION_FAILED"
            error_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
            print(f"\nFailed to run {tc['file']}: {error_msg}")
            
        res_file = os.path.join(results_dir, f"eval_{tc['degradation']}_{tc['duration']}s_{tc['start']:.1f}s_{base_name}.json")
        if exec_status == "SUCCESS" and os.path.exists(res_file):
            with open(res_file, 'r') as f:
                record = json.load(f)
            record["execution_status"] = "SUCCESS"
            record["error_message"] = ""
            summary_data.append(record)
        else:
            # Create a failed record
            summary_data.append({
                "query": base_name,
                "expected_state": tc["state"],
                "expected_track": tc["track"],
                "sample_duration": tc["duration"],
                "sample_start_position": tc["start"],
                "degradation": tc["degradation"],
                "predicted_track": "",
                "best_score": 0,
                "second_best_score": 0,
                "margin": 0,
                "decision": "",
                "correct_decision": False,
                "processing_time": 0.0,
                "execution_status": exec_status,
                "error_message": error_msg
            })
            
    print("\n\nEvaluation Complete.")
    
    csv_path = os.path.join(results_dir, "real_music_evaluation.csv")
    if summary_data:
        keys = summary_data[0].keys()
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(summary_data)
            
        print(f"\nResults saved to {csv_path}")
        
        # Calculate summary metrics safely
        def safe_acc(key, val, subset_filter=lambda x: x.get("expected_state") == "KNOWN"):
            subset = [r for r in summary_data if r.get(key) == val and subset_filter(r)]
            attempted = len(subset)
            executed = sum(1 for r in subset if r.get("execution_status") == "SUCCESS")
            failed = attempted - executed
            if executed == 0:
                return attempted, executed, failed, -1.0
            correct = sum(1 for r in subset if r.get("execution_status") == "SUCCESS" and r.get("correct_decision", False))
            return attempted, executed, failed, (correct / executed) * 100

        print("\n--- Identification Accuracy (KNOWN) ---")
        for deg in degradations:
            att, exe, fld, acc = safe_acc("degradation", deg)
            print(f"{deg}: Attempted: {att}, Executed: {exe}, Failed: {fld}")
            print(f"   Accuracy: {f'{acc:.1f}%' if acc >= 0 else 'N/A'}")
            
        print("\n--- Duration Accuracy (KNOWN) ---")
        for dur in durations:
            att, exe, fld, acc = safe_acc("sample_duration", dur)
            print(f"{dur}s: Attempted: {att}, Executed: {exe}, Failed: {fld}")
            print(f"   Accuracy: {f'{acc:.1f}%' if acc >= 0 else 'N/A'}")
            
        # Unknown Rejection Accuracy
        att, exe, fld, acc = safe_acc("expected_state", "UNKNOWN", lambda x: True)
        if att > 0:
            print(f"\n--- Unknown Rejection Accuracy ---")
            print(f"Attempted: {att}, Executed: {exe}, Failed: {fld}")
            print(f"Accuracy: {f'{acc:.1f}%' if acc >= 0 else 'N/A'}")
        else:
            print("\nUnknown Rejection Accuracy: N/A (no unknown queries)")

if __name__ == "__main__":
    run_real_evaluation()
