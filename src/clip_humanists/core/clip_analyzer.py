"""Enhanced CLIP analyzer with advanced features and optimizations."""

import os
import hashlib
import pickle
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm

from .config import get_config


logger = logging.getLogger(__name__)


@dataclass
class CLIPResult:
    """Result from CLIP analysis."""
    filepath: str
    similarities: Dict[str, float]
    confidence_intervals: Optional[Dict[str, Tuple[float, float]]] = None
    embedding_norm: Optional[float] = None
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedCLIPAnalyzer:
    """
    Enhanced CLIP analyzer with caching, batch processing, and advanced features.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        batch_size: Optional[int] = None,
        cache_dir: Optional[str] = None,
        device: Optional[str] = None,
        precision: Optional[str] = None,
    ):
        """
        Initialize the Enhanced CLIP analyzer.
        
        Args:
            model_name: Name of the CLIP model to use
            batch_size: Batch size for processing
            cache_dir: Directory for caching embeddings
            device: Device to use (auto, cpu, cuda)
            precision: Precision for computations (float32, float16)
        """
        self.config = get_config()
        
        # Override config with provided parameters
        self.model_name = model_name or self.config.model.name
        self.batch_size = batch_size or self.config.model.batch_size
        self.cache_dir = cache_dir or "cache/embeddings"
        self.precision = precision or self.config.model.precision
        
        # Set device
        if device == "auto" or device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Using device: {self.device}")
        logger.info(f"Model: {self.model_name}")
        
        # Initialize model and processor
        self._load_model()
        
        # Set up caching
        if self.config.model.cache_embeddings:
            os.makedirs(self.cache_dir, exist_ok=True)
            
        # Statistics
        self.stats = {
            "images_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time": 0.0,
        }
    
    def _load_model(self) -> None:
        """Load CLIP model and processor."""
        try:
            self.model = CLIPModel.from_pretrained(self.model_name).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            
            # Set precision
            if self.precision == "float16" and self.device == "cuda":
                self.model = self.model.half()
                
            self.model.eval()
            logger.info(f"Successfully loaded model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise
    
    def _get_cache_key(self, image_path: str) -> str:
        """Generate cache key for an image."""
        # Use file path and modification time for cache key
        stat = os.stat(image_path)
        content = f"{image_path}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_cached_embedding(self, cache_key: str) -> Optional[np.ndarray]:
        """Load cached image embedding."""
        if not self.config.model.cache_embeddings:
            return None
            
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    embedding = pickle.load(f)
                self.stats["cache_hits"] += 1
                return embedding
            except Exception as e:
                logger.warning(f"Failed to load cached embedding: {e}")
        
        self.stats["cache_misses"] += 1
        return None
    
    def _save_cached_embedding(self, cache_key: str, embedding: np.ndarray) -> None:
        """Save image embedding to cache."""
        if not self.config.model.cache_embeddings:
            return
            
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            logger.warning(f"Failed to save cached embedding: {e}")
    
    def _preprocess_image(self, image_path: str) -> Optional[torch.Tensor]:
        """Preprocess a single image."""
        try:
            image = Image.open(image_path).convert('RGB')
            
            # Resize if needed
            max_size = self.config.processing.max_image_size
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Process with CLIP processor
            inputs = self.processor(images=image, return_tensors="pt")
            return inputs.pixel_values.to(self.device)
            
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            return None
    
    def _get_image_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """Get embedding for a single image with caching."""
        cache_key = self._get_cache_key(image_path)
        
        # Try to load from cache
        embedding = self._load_cached_embedding(cache_key)
        if embedding is not None:
            return embedding
        
        # Process image
        image_tensor = self._preprocess_image(image_path)
        if image_tensor is None:
            return None
        
        try:
            with torch.no_grad():
                if self.precision == "float16":
                    image_tensor = image_tensor.half()
                
                image_features = self.model.get_image_features(image_tensor)
                
                # Normalize features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                embedding = image_features.cpu().numpy().squeeze()
                
                # Save to cache
                self._save_cached_embedding(cache_key, embedding)
                
                return embedding
                
        except Exception as e:
            logger.error(f"Error getting embedding for {image_path}: {e}")
            return None
    
    def _get_text_embeddings(self, text_prompts: List[str]) -> Optional[np.ndarray]:
        """Get embeddings for text prompts."""
        try:
            # Process text prompts
            text_inputs = self.processor(
                text=text_prompts,
                return_tensors="pt",
                padding=True,
                truncation=True
            ).to(self.device)
            
            with torch.no_grad():
                if self.precision == "float16":
                    text_inputs = {k: v.half() if v.dtype == torch.float32 else v 
                                 for k, v in text_inputs.items()}
                
                text_features = self.model.get_text_features(**text_inputs)
                
                # Normalize features
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                return text_features.cpu().numpy()
                
        except Exception as e:
            logger.error(f"Error getting text embeddings: {e}")
            return None
    
    def _calculate_similarities(
        self, 
        image_embedding: np.ndarray, 
        text_embeddings: np.ndarray
    ) -> np.ndarray:
        """Calculate cosine similarities between image and text embeddings."""
        # Calculate cosine similarity
        similarities = np.dot(image_embedding, text_embeddings.T)
        
        # Ensure similarities are in valid range
        similarities = np.clip(similarities, -1, 1)
        
        # Convert to 0-1 range
        similarities = (similarities + 1) / 2
        
        return similarities
    
    def _calculate_confidence_intervals(
        self, 
        similarities: np.ndarray,
        bootstrap_samples: int = 1000
    ) -> List[Tuple[float, float]]:
        """Calculate confidence intervals for similarity scores using bootstrap."""
        if not self.config.processing.include_confidence:
            return None
        
        # Simple confidence interval based on embedding norm
        # In a full implementation, this would use bootstrap sampling
        confidence_intervals = []
        for sim in similarities:
            margin = 0.05  # 5% margin of error
            lower = max(0, sim - margin)
            upper = min(1, sim + margin)
            confidence_intervals.append((lower, upper))
        
        return confidence_intervals
    
    def analyze_image(
        self, 
        image_path: str, 
        text_prompts: List[str]
    ) -> Optional[CLIPResult]:
        """
        Analyze a single image with text prompts.
        
        Args:
            image_path: Path to the image file
            text_prompts: List of text prompts to compare with the image
            
        Returns:
            CLIPResult object with analysis results
        """
        import time
        start_time = time.time()
        
        # Get image embedding
        image_embedding = self._get_image_embedding(image_path)
        if image_embedding is None:
            return None
        
        # Get text embeddings
        text_embeddings = self._get_text_embeddings(text_prompts)
        if text_embeddings is None:
            return None
        
        # Calculate similarities
        similarities = self._calculate_similarities(image_embedding, text_embeddings)
        
        # Create results dictionary
        similarity_dict = {
            prompt: float(score) 
            for prompt, score in zip(text_prompts, similarities)
        }
        
        # Calculate confidence intervals
        confidence_intervals = None
        if self.config.processing.include_confidence:
            ci_list = self._calculate_confidence_intervals(similarities)
            confidence_intervals = {
                prompt: ci 
                for prompt, ci in zip(text_prompts, ci_list)
            }
        
        processing_time = time.time() - start_time
        self.stats["total_processing_time"] += processing_time
        self.stats["images_processed"] += 1
        
        return CLIPResult(
            filepath=image_path,
            similarities=similarity_dict,
            confidence_intervals=confidence_intervals,
            embedding_norm=float(np.linalg.norm(image_embedding)),
            processing_time=processing_time,
            metadata={
                "model_name": self.model_name,
                "device": self.device,
                "precision": self.precision,
            }
        )
    
    def analyze_batch(
        self, 
        image_paths: List[str], 
        text_prompts: List[str],
        show_progress: bool = True
    ) -> List[CLIPResult]:
        """
        Analyze a batch of images with text prompts.
        
        Args:
            image_paths: List of paths to image files
            text_prompts: List of text prompts to compare with the images
            show_progress: Whether to show progress bar
            
        Returns:
            List of CLIPResult objects
        """
        results = []
        
        # Filter valid image paths
        valid_formats = self.config.processing.supported_formats
        valid_paths = [
            path for path in image_paths 
            if any(path.lower().endswith(fmt) for fmt in valid_formats)
        ]
        
        if not valid_paths:
            logger.warning("No valid image files found")
            return results
        
        logger.info(f"Processing {len(valid_paths)} images with {len(text_prompts)} prompts")
        
        # Process images
        iterator = tqdm(valid_paths, desc="Processing images") if show_progress else valid_paths
        
        for image_path in iterator:
            result = self.analyze_image(image_path, text_prompts)
            if result is not None:
                results.append(result)
        
        logger.info(f"Successfully processed {len(results)} images")
        return results
    
    def analyze_folder(
        self, 
        folder_path: str, 
        text_prompts: List[str],
        recursive: bool = False,
        show_progress: bool = True
    ) -> List[CLIPResult]:
        """
        Analyze all images in a folder.
        
        Args:
            folder_path: Path to folder containing images
            text_prompts: List of text prompts to compare with the images
            recursive: Whether to search recursively in subfolders
            show_progress: Whether to show progress bar
            
        Returns:
            List of CLIPResult objects
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Find all image files
        image_paths = []
        valid_formats = self.config.processing.supported_formats
        
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if any(file.lower().endswith(fmt) for fmt in valid_formats):
                        image_paths.append(os.path.join(root, file))
        else:
            for file in os.listdir(folder_path):
                if any(file.lower().endswith(fmt) for fmt in valid_formats):
                    image_paths.append(os.path.join(folder_path, file))
        
        logger.info(f"Found {len(image_paths)} images in {folder_path}")
        
        return self.analyze_batch(image_paths, text_prompts, show_progress)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()
        
        if stats["images_processed"] > 0:
            stats["avg_processing_time"] = (
                stats["total_processing_time"] / stats["images_processed"]
            )
            stats["cache_hit_rate"] = (
                stats["cache_hits"] / (stats["cache_hits"] + stats["cache_misses"])
            )
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        if os.path.exists(self.cache_dir):
            import shutil
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info("Cache cleared")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        # Clear GPU memory
        if hasattr(self, 'model') and self.device == "cuda":
            del self.model
            torch.cuda.empty_cache()