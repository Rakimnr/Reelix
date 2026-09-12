from typing import List
from models.recognition_result import MovieRecognitionResult

class FusionService:
    def fuse_movie_results(self, results: List[MovieRecognitionResult]) -> MovieRecognitionResult:
        # Simple fusion: prioritize MATCH over POSSIBLE over NO_MATCH
        # If external ever returns MATCH, it would win or tie-break here
        for state in ["MATCH", "POSSIBLE"]:
            for r in results:
                if r.state == state:
                    return r
        
        # If all NO_MATCH or SKIPPED, return the local one's result as default
        for r in results:
            if r.provider == "local_index":
                return r
                
        return results[0] if results else MovieRecognitionResult(state="NO_MATCH", provider="none")
