import cv2
import os

def extract_frames(video_path: str, output_dir: str, num_frames: int = 10) -> list[tuple[str, float]]:
    """
    Extracts frames from a video. Returns list of (frame_path, timestamp_seconds).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video {video_path}")
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if total_frames == 0 or fps == 0:
        return []
        
    step = max(1, total_frames // num_frames)
    extracted_data = []
    
    count = 0
    frame_idx = 0
    while cap.isOpened() and count < num_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
            
        timestamp_sec = frame_idx / fps
        out_path = os.path.join(output_dir, f"frame_{count:04d}.jpg")
        cv2.imwrite(out_path, frame)
        extracted_data.append((out_path, timestamp_sec))
        
        frame_idx += step
        count += 1
        
    cap.release()
    return extracted_data
