import os
import json
import csv
import sys
import subprocess
import glob

def run_batch():
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    known_clips = glob.glob("queries/known/*.mp4") + glob.glob("queries/known/*.mov")
    unknown_clips = glob.glob("queries/unknown/*.mp4") + glob.glob("queries/unknown/*.mov")
    
    test_cases = []
    
    for clip in known_clips:
        base = os.path.basename(clip).replace("_same.mp4", "").replace(".mp4", "")
        for deg in ["LIGHT", "MEDIUM", "HEAVY"]:
            test_cases.append({
                "file": clip, "state": "KNOWN", "title": base, "degradation": deg
            })
            
    for clip in unknown_clips:
        test_cases.append({
            "file": clip, "state": "UNKNOWN", "title": "", "degradation": "MEDIUM"
        })
        
    summary_data = []
    
    for tc in test_cases:
        print(f"\n======================================")
        print(f"Running {tc['state']} test for {os.path.basename(tc['file'])} [{tc['degradation']}]...")
        cmd = [
            sys.executable, "run_query.py", tc["file"],
            "--expected-state", tc["state"],
            "--expected-title", tc["title"],
            "--degradation", tc["degradation"]
        ]
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to run {tc['file']}")
            continue
        
        res_file = os.path.join(results_dir, f"eval_{tc['degradation']}_{os.path.basename(tc['file'])}.json")
        if os.path.exists(res_file):
            with open(res_file, 'r') as f:
                record = json.load(f)
                
            summary_data.append({
                "query": record.get("query_video"),
                "expected_state": record.get("expected_state"),
                "degradation": tc["degradation"],
                "predicted_title": record.get("best_title", ""),
                "best_similarity": round(record.get("best_raw_score", 0), 4),
                "second_best_similarity": round(record.get("second_best_score", 0), 4),
                "margin": round(record.get("margin", 0), 4),
                "supporting_frames": record.get("supporting_frames", 0),
                "visual_decision": record.get("visual_decision", ""),
                "ocr_detected": record.get("ocr_detected", False),
                "ocr_extracted_text": record.get("ocr_extracted_text", ""),
                "ocr_best_title": record.get("ocr_best_title", ""),
                "ocr_best_score": round(record.get("ocr_similarity", 0), 4),
                "visual_ocr_agreement": record.get("visual_ocr_agreement", False),
                "combined_decision": record.get("decision", ""),
                "correct_decision": record.get("correct_decision", False)
            })
            
    csv_path = os.path.join(results_dir, "ocr_evaluation_summary.csv")
    if summary_data:
        # Save specific OCR evaluation fields
        ocr_keys = [
            "query", "degradation", "best_similarity", "ocr_detected", 
            "ocr_extracted_text", "ocr_best_score", "visual_ocr_agreement", 
            "visual_decision", "combined_decision", "expected_state", "correct_decision"
        ]
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=ocr_keys, extrasaction='ignore')
            dict_writer.writeheader()
            dict_writer.writerows(summary_data)
        print(f"\nOCR Batch evaluation complete. Summary saved to {csv_path}")
        
        # OCR Analytics
        total_clips = len(summary_data)
        ocr_detected_count = sum(1 for row in summary_data if row["ocr_detected"])
        ocr_helped = sum(1 for row in summary_data if row["visual_decision"] == "POSSIBLE_MATCH" and row["combined_decision"] == "MATCH" and row["correct_decision"])
        ocr_disagreed = sum(1 for row in summary_data if row["ocr_detected"] and not row["visual_ocr_agreement"] and row["ocr_best_score"] > 0.4)
        
        print(f"\n--- OCR Impact Summary ---")
        print(f"Total queries: {total_clips}")
        print(f"Clips with usable OCR text: {ocr_detected_count} ({ocr_detected_count/total_clips*100:.1f}%)")
        print(f"Cases where OCR improved a decision: {ocr_helped}")
        print(f"Cases where OCR disagreed with visual: {ocr_disagreed}")
        
        # Print Aggregates
        known_scores = [row["best_similarity"] for row in summary_data if row["expected_state"] == "KNOWN"]
        unknown_scores = [row["best_similarity"] for row in summary_data if row["expected_state"] == "UNKNOWN"]
        
        print("\n--- Calibration Aggregates ---")
        
        if known_scores:
            print(f"KNOWN:")
            print(f"  Min Similarity: {min(known_scores):.4f}")
            print(f"  Avg Similarity: {sum(known_scores)/len(known_scores):.4f}")
            print(f"  Max Similarity: {max(known_scores):.4f}")
        
        if unknown_scores:
            print(f"\nUNKNOWN:")
            print(f"  Min Similarity: {min(unknown_scores):.4f}")
            print(f"  Avg Similarity: {sum(unknown_scores)/len(unknown_scores):.4f}")
            print(f"  Max Similarity: {max(unknown_scores):.4f}")
            
        if known_scores and unknown_scores:
            lowest_known = min(known_scores)
            highest_unknown = max(unknown_scores)
            print(f"\nScore Range Analysis:")
            print(f"  Lowest Known: {lowest_known:.4f}")
            print(f"  Highest Unknown: {highest_unknown:.4f}")
            
            if highest_unknown >= lowest_known:
                print("  WARNING: The known and unknown score distributions OVERLAP.")
                print("  Similarity threshold alone is INSUFFICIENT for perfect separation.")
            else:
                print("  The distributions do not overlap in this dataset.")
                print(f"  A safe threshold could exist between {highest_unknown:.4f} and {lowest_known:.4f}.")

if __name__ == "__main__":
    run_batch()
