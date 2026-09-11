import json
import os
import numpy as np

def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    else:
        return obj

def evaluate_and_save(expected_state: str, expected_title: str, query_video: str, degradation_level: str, diagnostics: dict, match_results: list, proc_time: float, output_path: str):
    
    decision = diagnostics['decision']
    best_title = diagnostics['best_title']
    
    if expected_state == "KNOWN":
        correct_decision = (decision in ["MATCH", "POSSIBLE_MATCH"]) and (expected_title.lower() == best_title.lower() if best_title else False)
    else:
        correct_decision = (decision == "NO_MATCH")
    
    record = {
        "query_video": os.path.basename(query_video),
        "expected_state": expected_state,
        "degradation_level": degradation_level,
        "expected_title": expected_title,
        "best_title": diagnostics['best_title'],
        "best_raw_score": diagnostics['best_score'],
        "second_best_score": diagnostics['second_best_score'],
        "margin": diagnostics['margin'],
        "supporting_frames": diagnostics['supporting_frames'],
        "visual_decision": diagnostics.get('visual_decision', decision),
        "ocr_detected": diagnostics.get('ocr_detected', False),
        "ocr_extracted_text": diagnostics.get('ocr_extracted_text', ""),
        "ocr_best_title": diagnostics.get('ocr_best_title'),
        "ocr_similarity": diagnostics.get('ocr_similarity', 0.0),
        "visual_ocr_agreement": diagnostics.get('visual_ocr_agreement', False),
        "decision": decision,
        "correct_decision": correct_decision,
        "processing_time_sec": round(proc_time, 2),
        "thresholds_used": diagnostics['thresholds'],
        "raw_results": match_results
    }
    
    sanitized_record = sanitize_for_json(record)
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(sanitized_record, f, indent=2)
        
    return sanitized_record
