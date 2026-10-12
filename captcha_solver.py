"""
==============================================================================
FILE HISTORY CARD
------------------------------------------------------------------------------
File:           captcha_solver.py
Author:         Asif Zaman
Created:        2026-10-12
Responsibility: Machine learning OCR inference module for solving image CAPTCHAs.
                Loads TrOCR (VisionEncoderDecoder) model and processor weights 
                from local disk for fast, offline prediction without network calls.
==============================================================================
"""

import os
from typing import Tuple, Optional
from PIL import Image

class CaptchaSolver:
    """
    Offline-first CAPTCHA solver using TrOCR model weights.
    Prioritizes local disk storage to avoid network requests and rate limits.
    """
    def __init__(self, local_model_dir: Optional[str] = None, hf_repo_id: str = "anuashok/ocr-captcha-v3"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.local_dir = local_model_dir or os.path.join(base_dir, "models", "ocr-captcha-v3")
        self.hf_repo_id = hf_repo_id
        self.processor = None
        self.model = None

    def load_model(self):
        """Loads TrOCR model and processor. Uses local disk if available; otherwise downloads and caches."""
        if self.model is not None and self.processor is not None:
            return

        from transformers import VisionEncoderDecoderModel, TrOCRProcessor, logging as hf_logging
        hf_logging.set_verbosity_error()

        # 1. Load from local directory (100% offline)
        weights_path = os.path.join(self.local_dir, "model.safetensors")
        if os.path.exists(weights_path):
            print(f"[CaptchaSolver] Loading model offline from: {self.local_dir}")
            self.processor = TrOCRProcessor.from_pretrained(self.local_dir, local_files_only=True)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.local_dir, local_files_only=True)
            print("[CaptchaSolver] Model ready.")
            return

        # 2. Download from Hugging Face and save locally
        print(f"[CaptchaSolver] Local weights not found. Downloading from Hugging Face: {self.hf_repo_id}...")
        self.processor = TrOCRProcessor.from_pretrained(self.hf_repo_id)
        self.model = VisionEncoderDecoderModel.from_pretrained(self.hf_repo_id)

        os.makedirs(self.local_dir, exist_ok=True)
        self.processor.save_pretrained(self.local_dir)
        self.model.save_pretrained(self.local_dir)
        print(f"[CaptchaSolver] Model saved locally to: {self.local_dir}")

    def warmup(self):
        """Preloads model weights into RAM for instant inference during automation."""
        self.load_model()

    def solve_image(self, image_path: str, max_digits: int = 4) -> Tuple[str, str]:
        """
        Runs OCR on an image file and returns (predicted_digits, raw_text).
        """
        self.load_model()
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Captcha image not found: {image_path}")

        # Ensure RGBA image on white background for clean OCR reading
        image = Image.open(image_path).convert("RGBA")
        background = Image.new("RGBA", image.size, (255, 255, 255))
        combined = Image.alpha_composite(background, image).convert("RGB")

        pixel_values = self.processor(combined, return_tensors="pt").pixel_values
        generated_ids = self.model.generate(pixel_values)
        predicted_raw = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        predicted_digits = ''.join(c for c in predicted_raw if c.isdigit())
        if max_digits:
            predicted_digits = predicted_digits[:max_digits]

        return predicted_digits, predicted_raw
