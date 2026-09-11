import os
import json
import csv
import sys
import subprocess
import glob

def run_batch():
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    known_clips = glob.glob("queries/known/*.*")
    unknown_clips = glob.glob("queries/unknown/*.*")
    
    test_cases = []
    
    durations = [5.0, 8.0, 10.0]
    degradations = ["CLEAN", "LIGHT", "MEDIUM", "HEAVY"]
    
    for clip in known_clips:
        if clip.endswith(".json") or clip.endswith(".csv"): continue
        base = os.path.basename(clip)
        track = os.path.splitext(base)[0].replace("_test", "").replace("_known", "")
        
        for dur in durations:
            for deg in degradations:
                test_cases.append({
                    "file": clip, "state": "KNOWN", "track": track,
                    "degradation": deg, "duration": dur, "start": 10.0
                })
                
    for clip in unknown_clips:
        if clip.endswith(".json") or clip.endswith(".csv"): continue
        base = os.path.basename(clip)
        test_cases.append({
            "file": clip, "state": "UNKNOWN", "track": "",
            "degradation": "MEDIUM", "duration": 8.0, "start": 0.0
        })
        
    summary_data = []
    
    for tc in test_cases:
        print(f"\n======================================")
        base_name = os.path.basename(tc['file'])
        print(f"Running {tc['state']} test: {base_name} [{tc['degradation']}, {tc['duration']}s]")
        cmd = [
            sys.executable, "run_music_query.py", tc["file"],
            "--expected-state", tc["state"],
            "--expected-track", tc["track"],
            "--degradation", tc["degradation"],
            "--duration", str(tc["duration"]),
            "--start-pos", str(tc["start"])
        ]
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to run {tc['file']}")
            continue
        
        res_file = os.path.join(results_dir, f"eval_{tc['degradation']}_{tc['duration']}s_{base_name}.json")
        if os.path.exists(res_file):
            with open(res_file, 'r') as f:
                record = json.load(f)
            summary_data.append(record)
            
    csv_path = os.path.join(results_dir, "music_evaluation_summary.csv")
    if summary_data:
        keys = summary_data[0].keys()
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(summary_data)
        print(f"\nBatch evaluation complete. Summary saved to {csv_path}")

if __name__ == "__main__":
    run_batch()
