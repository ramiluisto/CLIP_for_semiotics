"""
Utilities for comparing images with text using CLIP.
"""

from typing import Dict, List, Optional, Tuple, Union
import os
import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel


class ClipAnalyzer:
    """
    Class for analyzing images using CLIP model.
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize the CLIP analyzer.

        Args:
            model_name: Name of the CLIP model to use
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)

    def compare_image_with_texts(
        self, image_path: str, text_list: List[str]
    ) -> Dict[str, float]:
        """
        Compare an image with a list of text prompts.

        Args:
            image_path: Path to the image file
            text_list: List of text prompts to compare with the image

        Returns:
            Dictionary mapping text prompts to similarity scores
        """
        try:
            # Load and process the image
            image = Image.open(image_path)
            image_input = self.processor(images=image, return_tensors="pt").to(
                self.device
            )

            # Process the text prompts
            text_inputs = self.processor(
                text=text_list, return_tensors="pt", padding=True
            ).to(self.device)

            # Get features and calculate similarities
            with torch.no_grad():
                image_features = self.model.get_image_features(**image_input)
                text_features = self.model.get_text_features(**text_inputs)

                # Normalize features
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)

                # Calculate similarities
                similarities = (
                    (image_features @ text_features.T).squeeze().cpu().numpy()
                )

            # Create a dictionary of results
            if isinstance(similarities, np.ndarray):
                if similarities.ndim == 0:  # If there's only one text prompt
                    return {text_list[0]: float(similarities)}
                else:
                    return {
                        text: float(score)
                        for text, score in zip(text_list, similarities)
                    }
            else:
                # Handle case where similarities is a tensor
                if len(text_list) == 1:
                    return {text_list[0]: float(similarities)}
                else:
                    return {
                        text: float(score)
                        for text, score in zip(text_list, similarities)
                    }

        except Exception as e:
            print(f"Error comparing image {image_path} with texts: {e}")
            return {text: 0.0 for text in text_list}

    def analyze_folder(
        self, folder_path: str, text_list: List[str]
    ) -> List[Dict[str, Union[str, Dict[str, float]]]]:
        """
        Analyze all images in a folder.

        Args:
            folder_path: Path to the folder containing images
            text_list: List of text prompts to compare with the images

        Returns:
            List of dictionaries with filepath and similarity scores
        """
        if not os.path.exists(folder_path):
            raise ValueError(f"Folder path does not exist: {folder_path}")

        # List all jpg files in the folder
        jpg_files = [
            f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg"))
        ]

        # Create a list of dictionaries
        results = []
        for jpg_file in jpg_files:
            file_path = os.path.join(folder_path, jpg_file)
            similarities = self.compare_image_with_texts(file_path, text_list)

            results.append({"filepath": file_path, "similarities": similarities})

        return results
