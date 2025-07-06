"""OpenAI Vision API integration for multimodal content analysis."""

import os
import base64
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

try:
    import openai
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .rate_limiting import RateLimiter
from ..core.config import get_config


logger = logging.getLogger(__name__)


@dataclass
class VisionAnalysisResult:
    """Result from OpenAI Vision analysis."""
    filepath: str
    model_name: str
    timestamp: datetime
    qualitative_format: Dict[str, Any] = field(default_factory=dict)
    quantitative_format: Dict[str, Any] = field(default_factory=dict)
    raw_response: Optional[str] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class OpenAIVisionAnalyzer:
    """
    OpenAI Vision API client for multimodal content analysis.
    
    This class provides integration with OpenAI's vision-capable models
    for detailed image content analysis, complementing CLIP embeddings
    with structured qualitative and quantitative analysis.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        max_concurrent: int = 10,
        rate_limit_delay: float = 0.5,
        analysis_template: Optional[str] = None,
    ):
        """
        Initialize OpenAI Vision analyzer.
        
        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if None)
            model_name: Vision model to use (gpt-4o, gpt-4o-mini, gpt-4-vision-preview)
            max_concurrent: Maximum concurrent API requests
            rate_limit_delay: Delay between requests
            analysis_template: Custom analysis prompt template
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not available. Install with: pip install openai"
            )
        
        self.config = get_config()
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Initialize clients
        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            max_concurrent=max_concurrent,
            delay=rate_limit_delay
        )
        
        # Analysis template
        self.analysis_template = analysis_template or self._get_default_template()
        
        # Statistics
        self.stats = {
            "images_processed": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "total_api_calls": 0,
            "total_processing_time": 0.0,
        }
        
        logger.info(f"Initialized OpenAI Vision analyzer with model: {self.model_name}")
    
    def _get_default_template(self) -> str:
        """Get default analysis template."""
        return """
You are a specialist in multimodal content analysis. Analyze this image and provide structured analysis in JSON format.

Reply with one JSON object containing:
{
  "qualitative_format": {
    "description": "Detailed description of image content",
    "visual_elements": "Analysis of composition, color, style",
    "cultural_context": "Cultural and contextual interpretation",
    "narrative": "Story or message conveyed by the image"
  },
  "quantitative_format": {
    "objects": ["list", "of", "identified", "objects"],
    "colors": ["primary", "colors", "present"],
    "style": ["artistic", "style", "tokens"],
    "mood": ["emotional", "tone", "indicators"],
    "setting": ["location", "context", "markers"]
  }
}

Use lowercase snake_case for quantitative tokens. Provide rich detail in qualitative sections.
"""
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image as base64 string."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            raise
    
    def analyze_image(self, image_path: str) -> VisionAnalysisResult:
        """
        Analyze a single image using OpenAI Vision API.
        
        Args:
            image_path: Path to image file
            
        Returns:
            VisionAnalysisResult with analysis data
        """
        import time
        start_time = time.time()
        
        try:
            # Encode image
            base64_image = self._encode_image(image_path)
            
            # Prepare API request
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.analysis_template},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            # Make API call
            self.stats["total_api_calls"] += 1
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=4000,
                temperature=0.1
            )
            
            # Parse response
            raw_response = response.choices[0].message.content
            
            # Try to extract JSON from response
            analysis_data = self._parse_response(raw_response)
            
            processing_time = time.time() - start_time
            self.stats["total_processing_time"] += processing_time
            self.stats["images_processed"] += 1
            self.stats["successful_analyses"] += 1
            
            return VisionAnalysisResult(
                filepath=image_path,
                model_name=self.model_name,
                timestamp=datetime.now(),
                qualitative_format=analysis_data.get("qualitative_format", {}),
                quantitative_format=analysis_data.get("quantitative_format", {}),
                raw_response=raw_response,
                processing_time=processing_time,
                metadata={
                    "model": self.model_name,
                    "api_version": "v1",
                    "template_version": "default",
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats["total_processing_time"] += processing_time
            self.stats["images_processed"] += 1
            self.stats["failed_analyses"] += 1
            
            logger.error(f"Error analyzing image {image_path}: {e}")
            
            return VisionAnalysisResult(
                filepath=image_path,
                model_name=self.model_name,
                timestamp=datetime.now(),
                error=str(e),
                processing_time=processing_time,
            )
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from API."""
        import json
        import re
        
        try:
            # Try to find JSON in the response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r'(\{.*\})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Assume entire response is JSON
                    json_str = response.strip()
            
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Return a basic structure if parsing fails
            return {
                "qualitative_format": {
                    "description": response[:1000],  # First 1000 chars
                    "parsing_error": str(e)
                },
                "quantitative_format": {
                    "parsing_status": ["failed"],
                    "error_type": ["json_decode_error"]
                }
            }
    
    async def analyze_image_async(self, image_path: str) -> VisionAnalysisResult:
        """
        Async version of analyze_image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            VisionAnalysisResult with analysis data
        """
        import time
        start_time = time.time()
        
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()
            
            # Encode image
            base64_image = self._encode_image(image_path)
            
            # Prepare API request
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.analysis_template},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            # Make async API call
            self.stats["total_api_calls"] += 1
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=4000,
                temperature=0.1
            )
            
            # Parse response
            raw_response = response.choices[0].message.content
            analysis_data = self._parse_response(raw_response)
            
            processing_time = time.time() - start_time
            self.stats["total_processing_time"] += processing_time
            self.stats["images_processed"] += 1
            self.stats["successful_analyses"] += 1
            
            return VisionAnalysisResult(
                filepath=image_path,
                model_name=self.model_name,
                timestamp=datetime.now(),
                qualitative_format=analysis_data.get("qualitative_format", {}),
                quantitative_format=analysis_data.get("quantitative_format", {}),
                raw_response=raw_response,
                processing_time=processing_time,
                metadata={
                    "model": self.model_name,
                    "api_version": "v1",
                    "template_version": "default",
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats["total_processing_time"] += processing_time
            self.stats["images_processed"] += 1
            self.stats["failed_analyses"] += 1
            
            logger.error(f"Error analyzing image {image_path}: {e}")
            
            return VisionAnalysisResult(
                filepath=image_path,
                model_name=self.model_name,
                timestamp=datetime.now(),
                error=str(e),
                processing_time=processing_time,
            )
    
    async def analyze_batch_async(
        self, 
        image_paths: List[str],
        show_progress: bool = True
    ) -> List[VisionAnalysisResult]:
        """
        Analyze multiple images asynchronously.
        
        Args:
            image_paths: List of image file paths
            show_progress: Whether to show progress
            
        Returns:
            List of VisionAnalysisResult objects
        """
        if show_progress:
            from tqdm.asyncio import tqdm
            tasks = [
                self.analyze_image_async(path) 
                for path in image_paths
            ]
            results = await tqdm.gather(*tasks, desc="Analyzing images")
        else:
            results = await asyncio.gather(*[
                self.analyze_image_async(path) 
                for path in image_paths
            ])
        
        return results
    
    def analyze_folder(
        self,
        folder_path: str,
        recursive: bool = False,
        show_progress: bool = True
    ) -> List[VisionAnalysisResult]:
        """
        Analyze all images in a folder.
        
        Args:
            folder_path: Path to folder containing images
            recursive: Whether to search recursively
            show_progress: Whether to show progress
            
        Returns:
            List of VisionAnalysisResult objects
        """
        # Find image files
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
        
        # Analyze using async batch processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                self.analyze_batch_async(image_paths, show_progress)
            )
        finally:
            loop.close()
        
        return results
    
    def set_analysis_template(self, template: str) -> None:
        """Set custom analysis template."""
        self.analysis_template = template
        logger.info("Updated analysis template")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()
        
        if stats["images_processed"] > 0:
            stats["success_rate"] = (
                stats["successful_analyses"] / stats["images_processed"]
            )
            stats["avg_processing_time"] = (
                stats["total_processing_time"] / stats["images_processed"]
            )
        
        return stats
    
    def estimate_cost(self, num_images: int) -> Dict[str, float]:
        """
        Estimate API costs for analyzing images.
        
        Args:
            num_images: Number of images to analyze
            
        Returns:
            Cost estimates in USD
        """
        # Rough cost estimates (as of 2024)
        cost_per_image = {
            "gpt-4o": 0.15,
            "gpt-4o-mini": 0.02,
            "gpt-4-vision-preview": 0.30,
        }
        
        base_cost = cost_per_image.get(self.model_name, 0.05)
        
        return {
            "estimated_cost_usd": base_cost * num_images,
            "cost_per_image_usd": base_cost,
            "model": self.model_name,
            "num_images": num_images,
        }