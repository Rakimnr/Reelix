import os
import argparse
import time
import numpy as np
from src.reel_simulator import simulate_reel
from src.frame_extractor import extract_frames
from src.embedding_service import EmbeddingService
from src.index_builder import IndexBuilder
from src.query_matcher import QueryMatcher
from src.evaluator import evaluate_and_save
from src.cleanup import cleanup_temporary_files

def main():
    parser = argparse.ArgumentParser(description="Query the FAISS index with a degraded Reel clip.")
    parser.add_argument("query_video", help="Path to the query clip")
    parser.add_argument("--expected-state", default="KNOWN", choices=["KNOWN", "UNKNOWN"], help="Expected state for evaluation")
    parser.add_argument("--expected-title", default="", help="Expected title for known clips")
    parser.add_argument("--degradation", default="MEDIUM", choices=["LIGHT", "MEDIUM", "HEAVY"], help="Degradation severity preset")
    parser.add_argument("--index-dir", default="index", help="Directory containing the index")
    parser.add_argument("--match-threshold", type=float, default=0.85, help="Threshold for MATCH")
    parser.add_argument("--possible-threshold", type=float, default=0.75, help="Threshold for POSSIBLE_MATCH")
    parser.add_argument("--keep-temp", action="store_true", help="Do not delete temporary files")
    
    args = parser.parse_args()
    
    temp_sim_dir = "extracted/queries/simulated"
    temp_frames_dir = "extracted/queries/frames"
    os.makedirs("results", exist_ok=True)
    
    start_time = time.time()
    
    try:
        print(f"1. Simulating {args.degradation} degraded Reel...")
        degraded_path = simulate_reel(args.query_video, temp_sim_dir, degradation=args.degradation)
        
        print("2. Extracting query frames...")
        frame_data = extract_frames(degraded_path, temp_frames_dir, num_frames=6)
        
        print("3. Generating query embeddings and OCR...")
        embedder = EmbeddingService()
        from src.ocr_service import OCRService
        ocr_service = OCRService()
        
        query_embeddings = []
        query_ocr_texts = []
        for f_path, _ in frame_data:
            query_embeddings.append(embedder.get_embedding(f_path))
            _, clean_text = ocr_service.extract_text(f_path)
            query_ocr_texts.append(clean_text)
        
        if not query_embeddings:
            raise ValueError("No frames extracted from query video.")
            
        query_matrix = np.vstack(query_embeddings)
        
        print("4. Searching index...")
        index_builder = IndexBuilder()
        index_builder.load(
            os.path.join(args.index_dir, "visual.index"),
            os.path.join(args.index_dir, "metadata.json")
        )
        
        matcher = QueryMatcher(index_builder)
        diagnostics, results = matcher.search(
            query_matrix, 
            query_ocr_texts=query_ocr_texts,
            top_k=5, 
            match_threshold=args.match_threshold, 
            possible_threshold=args.possible_threshold
        )
        
        proc_time = time.time() - start_time
        
        print("5. Evaluating results...")
        res_file = os.path.join("results", f"eval_{args.degradation}_{os.path.basename(args.query_video)}.json")
        record = evaluate_and_save(
            args.expected_state, 
            args.expected_title, 
            args.query_video, 
            args.degradation,
            diagnostics, 
            results, 
            proc_time, 
            res_file
        )
        
        print("\n--- FAISS & OCR Recognition Results ---")
        print(f"Query: {record['query_video']} [{args.degradation}]")
        print(f"Visual Match: {record['best_title']} (Score: {record['best_raw_score']:.4f})")
        print(f"OCR Detected: {record['ocr_detected']}")
        if record['ocr_detected']:
            print(f"OCR Best Title: {record['ocr_best_title']} (Score: {record['ocr_similarity']:.4f})")
            print(f"OCR Text: {record['ocr_extracted_text'][:100]}...")
            print(f"Visual/OCR Agreement: {record['visual_ocr_agreement']}")
        print(f"Visual Decision: {record['visual_decision']}")
        print(f"Combined Decision: {record['decision']} (Expected: {record['expected_state']})")
        print(f"Correct Decision: {record['correct_decision']}")
        print(f"Processing time: {record['processing_time_sec']}s")
        print(f"Full details saved to: {res_file}\n")
        
    finally:
        if not args.keep_temp:
            cleanup_temporary_files(temp_sim_dir, temp_frames_dir)

if __name__ == "__main__":
    main()
