import os
from typing import List, Tuple

class FrameSelector:
    def __init__(self):
        try:
            import cv2
            self.has_cv2 = True
        except ImportError:
            self.has_cv2 = False

    def select_best_frame(self, frame_paths: List[str]) -> Tuple[str, float, str]:
        if not frame_paths:
            return "", 0.0, "no_frames"
            
        if len(frame_paths) == 1:
            return frame_paths[0], 1.0, "only_frame"
            
        best_frame = frame_paths[0]
        best_score = -1.0
        
        if self.has_cv2:
            import cv2
            for path in frame_paths:
                img = cv2.imread(path)
                if img is None:
                    continue
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # Variance of Laplacian for sharpness
                score = cv2.Laplacian(gray, cv2.CV_64F).var()
                if score > best_score:
                    best_score = score
                    best_frame = path
            reason = "laplacian_variance"
        else:
            # Fallback: file size proxy for entropy/richness
            for path in frame_paths:
                score = float(os.path.getsize(path))
                if score > best_score:
                    best_score = score
                    best_frame = path
            reason = "file_size_entropy_proxy"
            
        print(f"[FRAME_SELECTOR] selected={os.path.basename(best_frame)} score={best_score:.2f} reason={reason}")
        return best_frame, best_score, reason
