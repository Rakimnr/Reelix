import numpy as np
from collections import defaultdict

class QueryMatcher:
    def __init__(self, index_builder):
        self.index_builder = index_builder

    def search(self, query_embeddings: np.ndarray, query_ocr_texts: list = None, top_k: int = 5, match_threshold: float = 0.85, possible_threshold: float = 0.75):
        from src.text_matcher import compute_text_similarity
        
        D, I = self.index_builder.index.search(query_embeddings, top_k)
        
        title_scores = defaultdict(float)
        title_supporting_frames = defaultdict(set)
        title_matches = defaultdict(list)
        
        # OCR tracking
        ocr_title_scores = defaultdict(float)
        
        for q_idx in range(len(query_embeddings)):
            q_ocr = query_ocr_texts[q_idx] if query_ocr_texts else ""
            
            for k in range(top_k):
                ref_idx = I[q_idx][k]
                distance = D[q_idx][k]
                if ref_idx != -1:
                    meta = self.index_builder.metadata[ref_idx]
                    title = meta['title']
                    ref_ocr = meta.get('ocr_text_clean', "")
                    
                    similarity = float(max(0.0, 1.0 - (distance / 2.0)))
                    
                    if similarity > title_scores[title]:
                        title_scores[title] = similarity
                        
                    title_supporting_frames[title].add(q_idx)
                        
                    title_matches[title].append({
                        "similarity": similarity,
                        "timestamp": meta['timestamp'],
                        "clip_id": meta['clip_id'],
                        "query_frame_idx": q_idx
                    })
                    
                    # Track best OCR similarity for this title
                    if q_ocr and ref_ocr:
                        text_sim = compute_text_similarity(q_ocr, ref_ocr)
                        if text_sim > ocr_title_scores[title]:
                            ocr_title_scores[title] = text_sim
                            
        sorted_titles = sorted(title_scores.items(), key=lambda x: x[1], reverse=True)
        
        best_title = None
        best_score = 0.0
        second_best_score = 0.0
        margin = 0.0
        supporting_frames = 0
        visual_decision = "NO_MATCH"
        
        if sorted_titles:
            best_title = sorted_titles[0][0]
            best_score = sorted_titles[0][1]
            supporting_frames = len(title_supporting_frames[best_title])
            
            if len(sorted_titles) > 1:
                second_best_score = sorted_titles[1][1]
                margin = best_score - second_best_score
            else:
                margin = best_score
                
            if best_score >= match_threshold:
                visual_decision = "MATCH"
            elif best_score >= possible_threshold:
                visual_decision = "POSSIBLE_MATCH"
                
        # Calculate OCR stats
        ocr_available = bool(query_ocr_texts and any(query_ocr_texts))
        ocr_extracted_text = " | ".join([t for t in (query_ocr_texts or []) if t])
        
        ocr_best_title = None
        ocr_best_score = 0.0
        if ocr_title_scores:
            sorted_ocr = sorted(ocr_title_scores.items(), key=lambda x: x[1], reverse=True)
            ocr_best_title = sorted_ocr[0][0]
            ocr_best_score = sorted_ocr[0][1]
            
        # EXPERIMENTAL FUSION LOGIC
        combined_decision = visual_decision
        visual_ocr_agreement = False
        
        if visual_decision != "NO_MATCH" and ocr_best_score > 0.4: # Arbitrary text sim threshold
            if ocr_best_title == best_title:
                visual_ocr_agreement = True
                if visual_decision == "POSSIBLE_MATCH":
                    # OCR agreement can strengthen it
                    combined_decision = "MATCH"
            else:
                # Disagreement! Downgrade to possible or uncertain
                combined_decision = "POSSIBLE_MATCH"
        
        results = []
        for title, score in sorted_titles:
            results.append({
                "title": title,
                "best_similarity": score,
                "supporting_frames": len(title_supporting_frames[title]),
                "matches": sorted(title_matches[title], key=lambda x: x['similarity'], reverse=True)[:3]
            })
            
        diagnostics = {
            "best_title": best_title,
            "best_score": best_score,
            "second_best_score": second_best_score,
            "margin": margin,
            "supporting_frames": supporting_frames,
            "visual_decision": visual_decision,
            "decision": combined_decision,  # Use the fused decision as primary
            "ocr_detected": ocr_available,
            "ocr_extracted_text": ocr_extracted_text,
            "ocr_best_title": ocr_best_title,
            "ocr_similarity": ocr_best_score,
            "visual_ocr_agreement": visual_ocr_agreement,
            "thresholds": {
                "match": match_threshold,
                "possible": possible_threshold
            }
        }
            
        return diagnostics, results
            
        return diagnostics, results
