from collections import defaultdict
import numpy as np

class MusicMatcher:
    def __init__(self, catalogue):
        self.catalogue = catalogue
        
    def match(self, query_hashes: list):
        if not query_hashes:
            return "NO_MATCH", None, 0, 0, 0, 0
            
        # Create a dict of hash -> list of query_offsets
        q_hash_map = defaultdict(list)
        for h_str, offset in query_hashes:
            q_hash_map[h_str].append(offset)
            
        # Query DB for all matching hashes
        db_matches = self.catalogue.find_matches(query_hashes)
        
        # We need to find consistent relative timing.
        # delta = db_offset - query_offset.
        # True matches will have many hits at the same delta.
        track_deltas = defaultdict(list)
        
        for db_hash, db_offset, track_id in db_matches:
            if db_hash in q_hash_map:
                for q_offset in q_hash_map[db_hash]:
                    db_off = db_offset
                    if isinstance(db_off, bytes):
                        db_off = int.from_bytes(db_off, byteorder='little')
                    
                    q_off = q_offset
                    if isinstance(q_off, bytes):
                        q_off = int.from_bytes(q_off, byteorder='little')
                        
                    delta = int(db_off) - int(q_off)
                    track_deltas[track_id].append(delta)
                    
        # Evaluate tracks
        track_scores = {}
        for track_id, deltas in track_deltas.items():
            if not deltas:
                continue
            # Find the most common delta (using a small histogram/binning)
            # Since offsets are integer bins, we can use exact match or small bin tolerance
            # Let's use exact match or +/- 1 for robustness
            deltas = np.array(deltas)
            # Simple histogram count
            counts = defaultdict(int)
            for d in deltas:
                counts[d] += 1
            
            best_delta = max(counts, key=counts.get)
            best_score = counts[best_delta]
            track_scores[track_id] = {
                "score": best_score,
                "offset": best_delta,
                "total_matches": len(deltas)
            }
            
        if not track_scores:
            return "NO_MATCH", None, 0, 0, 0, 0
            
        # Sort by best score
        sorted_tracks = sorted(track_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        best_track_id = sorted_tracks[0][0]
        best_score = sorted_tracks[0][1]['score']
        best_offset = sorted_tracks[0][1]['offset']
        
        second_best_score = 0
        margin = best_score
        
        if len(sorted_tracks) > 1:
            second_best_score = sorted_tracks[1][1]['score']
            margin = best_score - second_best_score
            
        # Experimental thresholds. 
        # Hashes are plentiful, so a true match usually gets 10-100s of consistent deltas.
        # We will use 10 for MATCH, 5 for POSSIBLE_MATCH
        decision = "NO_MATCH"
        if best_score >= 10:
            decision = "MATCH"
        elif best_score >= 5:
            decision = "POSSIBLE_MATCH"
            
        return decision, best_track_id, best_score, second_best_score, margin, best_offset
