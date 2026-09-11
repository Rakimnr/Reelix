import os
import argparse
import numpy as np
from src.frame_extractor import extract_frames
from src.embedding_service import EmbeddingService
from src.index_builder import IndexBuilder
from src.ocr_service import OCRService

def main():
    parser = argparse.ArgumentParser(description="Build FAISS visual index from reference clips.")
    parser.add_argument("--ref-dir", default="references", help="Directory containing reference clips")
    parser.add_argument("--index-dir", default="index", help="Directory to save index")
    parser.add_argument("--frames-per-clip", type=int, default=15, help="Number of frames to extract per clip")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.index_dir):
        os.makedirs(args.index_dir)
        
    temp_extract_dir = "extracted/references"
    
    print("Initializing embedding service...")
    embedder = EmbeddingService()
    ocr_service = OCRService()
    
    index_builder = IndexBuilder(embedding_dim=512) 
    
    all_embeddings = []
    all_metadata = []
    
    os.makedirs(args.ref_dir, exist_ok=True)
    
    for filename in os.listdir(args.ref_dir):
        if not filename.endswith((".mp4", ".mov", ".mkv")):
            continue
            
        filepath = os.path.join(args.ref_dir, filename)
        title = os.path.splitext(filename)[0]
        print(f"Processing reference: {title}")
        
        clip_extract_dir = os.path.join(temp_extract_dir, title)
        frame_data = extract_frames(filepath, clip_extract_dir, num_frames=args.frames_per_clip)
        
        for frame_path, timestamp in frame_data:
            emb = embedder.get_embedding(frame_path)
            raw_text, clean_text = ocr_service.extract_text(frame_path)
            
            all_embeddings.append(emb)
            all_metadata.append({
                "clip_id": filename,
                "title": title,
                "timestamp": float(timestamp),
                "ocr_text_clean": clean_text
            })
            
    if not all_embeddings:
        print(f"No valid reference clips found in {args.ref_dir}/")
        return
        
    embeddings_matrix = np.vstack(all_embeddings)
    index_builder.add_embeddings(embeddings_matrix, all_metadata)
    
    index_builder.save(
        os.path.join(args.index_dir, "visual.index"),
        os.path.join(args.index_dir, "metadata.json")
    )
    
    print(f"Index built successfully with {len(all_metadata)} total frames.")

    
if __name__ == "__main__":
    main()
