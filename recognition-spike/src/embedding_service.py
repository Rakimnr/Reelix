import torch
from PIL import Image
import open_clip
import numpy as np

class EmbeddingService:
    def __init__(self, model_name="ViT-B-32", pretrained="laion2b_s34b_b79k"):
        print(f"Loading OpenCLIP model {model_name}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(model_name, pretrained=pretrained)
        self.model = self.model.to(self.device)
        self.model.eval()

    def get_embedding(self, image_path: str) -> np.ndarray:
        image = Image.open(image_path).convert("RGB")
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            
        # Normalize
        image_features /= image_features.norm(dim=-1, keepdim=True)
        # Convert to numpy array float32
        return image_features.cpu().numpy().astype(np.float32)[0]
