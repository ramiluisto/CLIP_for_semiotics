"""
CLIP service for image-text similarity analysis.
Adapted from src/clip_utils.py for Django.
"""

from django.conf import settings
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ClipService:
    """
    Singleton service for CLIP model operations.
    Model is loaded once and reused for efficiency.
    """
    _instance = None
    _model = None
    _processor = None
    _device = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize CLIP model and processor."""
        # Determine device
        device_setting = settings.CLIP_DEVICE
        if device_setting == 'auto':
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self._device = device_setting

        model_name = settings.CLIP_MODEL_NAME

        logger.info(f"Loading CLIP model: {model_name} on device: {self._device}")

        try:
            self._model = CLIPModel.from_pretrained(model_name).to(self._device)
            self._processor = CLIPProcessor.from_pretrained(model_name)
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading CLIP model: {e}")
            raise

    def compare_image_with_texts(
        self,
        image_path: str,
        text_list: List[str]
    ) -> Dict[str, float]:
        """
        Compare an image with multiple text prompts.

        Args:
            image_path: Path to image file
            text_list: List of text prompts

        Returns:
            Dictionary mapping text prompts to similarity scores
        """
        try:
            # Load and process image
            image = Image.open(image_path)

            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                image = image.convert('RGB')

            image_input = self._processor(
                images=image,
                return_tensors="pt"
            ).to(self._device)

            # Process text
            text_inputs = self._processor(
                text=text_list,
                return_tensors="pt",
                padding=True
            ).to(self._device)

            # Calculate similarities
            with torch.no_grad():
                image_features = self._model.get_image_features(**image_input)
                text_features = self._model.get_text_features(**text_inputs)

                # Normalize
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)

                # Calculate similarities
                similarities = (
                    (image_features @ text_features.T).squeeze().cpu().numpy()
                )

            # Format results
            if isinstance(similarities, np.ndarray):
                if similarities.ndim == 0:  # Single text prompt
                    return {text_list[0]: float(similarities)}
                else:
                    return {
                        text: float(score)
                        for text, score in zip(text_list, similarities)
                    }
            else:
                # Handle scalar case
                if len(text_list) == 1:
                    return {text_list[0]: float(similarities)}
                else:
                    return {
                        text: float(score)
                        for text, score in zip(text_list, similarities)
                    }

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            # Return zero scores on error
            return {text: 0.0 for text in text_list}

    def batch_process_images(
        self,
        image_paths: List[str],
        text_list: List[str],
        progress_callback=None
    ) -> List[Dict]:
        """
        Process multiple images in batch.

        Args:
            image_paths: List of image file paths
            text_list: List of text prompts
            progress_callback: Optional callback function(current, total)

        Returns:
            List of results dictionaries
        """
        results = []
        total = len(image_paths)

        for idx, img_path in enumerate(image_paths):
            similarities = self.compare_image_with_texts(img_path, text_list)
            results.append({
                'filepath': img_path,
                'similarities': similarities
            })

            if progress_callback:
                progress_callback(idx + 1, total)

            # Log progress
            if (idx + 1) % 10 == 0 or idx + 1 == total:
                logger.info(f"Processed {idx + 1}/{total} images")

        return results

    def get_device(self):
        """Get the device being used for processing."""
        return self._device

    def get_model_name(self):
        """Get the name of the loaded model."""
        return settings.CLIP_MODEL_NAME

    def cleanup(self):
        """Clean up resources (free GPU memory)."""
        if self._model is not None:
            del self._model
            self._model = None
        if self._processor is not None:
            del self._processor
            self._processor = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("CLIP service resources cleaned up")


# Create a singleton instance
_clip_service_instance = None


def get_clip_service() -> ClipService:
    """Get the singleton ClipService instance."""
    global _clip_service_instance
    if _clip_service_instance is None:
        _clip_service_instance = ClipService()
    return _clip_service_instance
