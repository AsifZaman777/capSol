"""
==============================================================================
FILE HISTORY CARD
------------------------------------------------------------------------------
File:           download_model.py
Author:         Asif Zaman
Created:        2026-10-12
Responsibility: Setup and provisioning utility. Downloads the TrOCR model weights
                from Hugging Face once and saves them into the local './models/'
                directory to enable 100% offline execution for the framework.
==============================================================================
"""

import os
from transformers import VisionEncoderDecoderModel, TrOCRProcessor

def download_and_cache_model(
    repo_id: str = "anuashok/ocr-captcha-v3",
    destination_dir: str = "./models/ocr-captcha-v3"
):
    os.makedirs(destination_dir, exist_ok=True)
    print(f"Downloading model '{repo_id}' from Hugging Face...")
    
    processor = TrOCRProcessor.from_pretrained(repo_id)
    model = VisionEncoderDecoderModel.from_pretrained(repo_id)

    print(f"Saving model files to local directory: {destination_dir}...")
    processor.save_pretrained(destination_dir)
    model.save_pretrained(destination_dir)
    
    print("Model downloaded and saved locally! You can now run the framework offline.")

if __name__ == "__main__":
    download_and_cache_model()
