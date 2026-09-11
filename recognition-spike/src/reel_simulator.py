import cv2
import os

def simulate_reel(video_path: str, output_dir: str, degradation: str = "MEDIUM") -> str:
    """Simulates common Reel conditions: vertical crop, reduced resolution, moderate compression, overlay."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    out_path = os.path.join(output_dir, f"simulated_{degradation.lower()}_" + os.path.basename(video_path))
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video {video_path}")
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if degradation == "LIGHT":
        crop_ratio = 10/16
        out_height = 1080
        text_scale = 1
        text_thickness = 2
        overlay_text = "Wait for it..."
        contrast = 1.0
        brightness = 0
    elif degradation == "HEAVY":
        crop_ratio = 8/16
        out_height = 480
        text_scale = 2
        text_thickness = 3
        overlay_text = "MUST WATCH TILL END!!!"
        contrast = 1.2
        brightness = 15
    else: # MEDIUM
        crop_ratio = 9/16
        out_height = 720
        text_scale = 1.5
        text_thickness = 2
        overlay_text = "@reel_creator"
        contrast = 1.0
        brightness = 0
        
    target_width = int(height * crop_ratio)
    start_x = max(0, (width - target_width) // 2)
    out_width = int(target_width * (out_height / height))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (out_width, out_height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        cropped = frame[:, start_x:start_x+target_width]
        resized = cv2.resize(cropped, (out_width, out_height))
        
        if contrast != 1.0 or brightness != 0:
            resized = cv2.convertScaleAbs(resized, alpha=contrast, beta=brightness)
            
        cv2.putText(resized, overlay_text, (int(out_width*0.1), int(out_height*0.2)), 
                    cv2.FONT_HERSHEY_SIMPLEX, text_scale, (255, 255, 255), text_thickness)
        
        if degradation == "HEAVY":
            cv2.rectangle(resized, (0, int(out_height*0.8)), (out_width, out_height), (0,0,0), -1)
            cv2.putText(resized, "Link in bio", (int(out_width*0.2), int(out_height*0.9)), 
                        cv2.FONT_HERSHEY_SIMPLEX, text_scale, (0, 255, 255), text_thickness)
        
        out.write(resized)
        
    cap.release()
    out.release()
    return out_path
