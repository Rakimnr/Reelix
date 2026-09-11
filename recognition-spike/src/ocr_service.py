import os
import cv2
import pytesseract
import re

class OCRService:
    def __init__(self):
        self.tess_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(self.tess_path):
            pytesseract.pytesseract.tesseract_cmd = self.tess_path
            
        self.is_available = self._check_path()
        if not self.is_available:
            print("WARNING: Tesseract is unavailable. OCR evidence will be skipped.")

    def _check_path(self):
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def preprocess_image(self, image_path):
        """Lightweight preprocessing: grayscale."""
        img = cv2.imread(image_path)
        if img is None:
            return None
        # Simple grayscale for now. Thresholding can sometimes destroy text if not careful.
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return gray

    def extract_text(self, image_path):
        if not self.is_available:
            return "", ""
            
        processed_img = self.preprocess_image(image_path)
        if processed_img is None:
            return "", ""
            
        try:
            raw_text = pytesseract.image_to_string(processed_img)
        except Exception as e:
            print(f"OCR failed on {image_path}: {e}")
            return "", ""
        
        # Clean text: remove extra whitespace and newlines, keep basic punctuation
        clean_text = re.sub(r'\s+', ' ', raw_text)
        # We'll allow letters, numbers, spaces, and basic punctuation
        clean_text = re.sub(r'[^\w\s\.,!\?\'\"]', '', clean_text).strip()
        
        return raw_text, clean_text
