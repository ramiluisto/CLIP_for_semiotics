"""Multimodal content analysis combining CLIP and OpenAI Vision."""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import os

from ..core.clip_analyzer import CLIPResult, EnhancedCLIPAnalyzer
from ..core.gps_extractor import GPSResult, GPSExtractor
from ..apis.openai_vision import OpenAIVisionAnalyzer, VisionAnalysisResult


logger = logging.getLogger(__name__)


@dataclass
class MultimodalResult:
    """Combined result from CLIP and Vision analysis."""
    filepath: str
    timestamp: datetime
    clip_result: Optional[CLIPResult] = None
    vision_result: Optional[VisionAnalysisResult] = None
    gps_result: Optional[GPSResult] = None
    combined_analysis: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MultimodalContentAnalyzer:
    """
    Combined multimodal content analyzer using CLIP embeddings and OpenAI Vision.
    
    This class integrates CLIP-based similarity analysis with detailed
    OpenAI Vision content analysis to provide comprehensive image understanding
    suitable for digital humanities research.
    """
    
    def __init__(
        self,
        clip_analyzer: Optional[EnhancedCLIPAnalyzer] = None,
        vision_analyzer: Optional[OpenAIVisionAnalyzer] = None,
        gps_extractor: Optional[GPSExtractor] = None,
        enable_clip: bool = True,
        enable_vision: bool = True,
        enable_gps: bool = True,
    ):
        """
        Initialize multimodal content analyzer.
        
        Args:
            clip_analyzer: CLIP analyzer instance
            vision_analyzer: OpenAI Vision analyzer instance  
            gps_extractor: GPS extractor instance
            enable_clip: Whether to perform CLIP analysis
            enable_vision: Whether to perform Vision analysis
            enable_gps: Whether to extract GPS data
        """
        self.enable_clip = enable_clip
        self.enable_vision = enable_vision
        self.enable_gps = enable_gps
        
        # Initialize analyzers
        self.clip_analyzer = clip_analyzer or (
            EnhancedCLIPAnalyzer() if enable_clip else None
        )
        self.vision_analyzer = vision_analyzer or (
            OpenAIVisionAnalyzer() if enable_vision else None
        )
        self.gps_extractor = gps_extractor or (
            GPSExtractor() if enable_gps else None
        )
        
        # Statistics
        self.stats = {
            "images_processed": 0,
            "clip_analyses": 0,
            "vision_analyses": 0,
            "gps_extractions": 0,
            "combined_analyses": 0,
            "errors": 0,
        }
        
        logger.info(f"Initialized MultimodalContentAnalyzer with:")
        logger.info(f"  CLIP: {'enabled' if enable_clip else 'disabled'}")
        logger.info(f"  Vision: {'enabled' if enable_vision else 'disabled'}")
        logger.info(f"  GPS: {'enabled' if enable_gps else 'disabled'}")
    
    def analyze_image(
        self,
        image_path: str,
        clip_prompts: Optional[List[str]] = None,
        vision_template: Optional[str] = None,
    ) -> MultimodalResult:
        """
        Perform comprehensive multimodal analysis of a single image.
        
        Args:
            image_path: Path to image file
            clip_prompts: Text prompts for CLIP analysis
            vision_template: Custom template for Vision analysis
            
        Returns:
            MultimodalResult with all analysis data
        """
        result = MultimodalResult(
            filepath=image_path,
            timestamp=datetime.now(),
        )
        
        # CLIP Analysis
        if self.enable_clip and self.clip_analyzer and clip_prompts:
            try:
                clip_result = self.clip_analyzer.analyze_image(image_path, clip_prompts)
                result.clip_result = clip_result
                self.stats["clip_analyses"] += 1
                logger.debug(f"CLIP analysis completed for {image_path}")
            except Exception as e:
                logger.error(f"CLIP analysis failed for {image_path}: {e}")
                self.stats["errors"] += 1
        
        # Vision Analysis
        if self.enable_vision and self.vision_analyzer:
            try:
                if vision_template:
                    original_template = self.vision_analyzer.analysis_template
                    self.vision_analyzer.set_analysis_template(vision_template)
                
                vision_result = self.vision_analyzer.analyze_image(image_path)
                result.vision_result = vision_result
                self.stats["vision_analyses"] += 1
                logger.debug(f"Vision analysis completed for {image_path}")
                
                if vision_template:
                    self.vision_analyzer.set_analysis_template(original_template)
                    
            except Exception as e:
                logger.error(f"Vision analysis failed for {image_path}: {e}")
                self.stats["errors"] += 1
        
        # GPS Extraction
        if self.enable_gps and self.gps_extractor:
            try:
                gps_result = self.gps_extractor.extract_gps_data(image_path)
                result.gps_result = gps_result
                self.stats["gps_extractions"] += 1
                logger.debug(f"GPS extraction completed for {image_path}")
            except Exception as e:
                logger.error(f"GPS extraction failed for {image_path}: {e}")
                self.stats["errors"] += 1
        
        # Combined Analysis
        result.combined_analysis = self._create_combined_analysis(result)
        self.stats["combined_analyses"] += 1
        self.stats["images_processed"] += 1
        
        return result
    
    def _create_combined_analysis(self, result: MultimodalResult) -> Dict[str, Any]:
        """Create combined analysis from all available data."""
        combined = {
            "filepath": result.filepath,
            "timestamp": result.timestamp.isoformat(),
            "analysis_methods": [],
        }
        
        # Add CLIP data
        if result.clip_result:
            combined["analysis_methods"].append("clip")
            combined["clip_similarities"] = result.clip_result.similarities
            combined["clip_metadata"] = result.clip_result.metadata
            
            # Find dominant themes from CLIP
            if result.clip_result.similarities:
                sorted_similarities = sorted(
                    result.clip_result.similarities.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                combined["dominant_themes"] = [
                    {"theme": theme, "similarity": score}
                    for theme, score in sorted_similarities[:3]
                ]
        
        # Add Vision data
        if result.vision_result and not result.vision_result.error:
            combined["analysis_methods"].append("vision")
            combined["qualitative_analysis"] = result.vision_result.qualitative_format
            combined["quantitative_tokens"] = result.vision_result.quantitative_format
            
            # Extract key elements from vision analysis
            if result.vision_result.quantitative_format:
                quant = result.vision_result.quantitative_format
                combined["detected_objects"] = quant.get("objects", [])
                combined["visual_style"] = quant.get("style", [])
                combined["dominant_colors"] = quant.get("colors", [])
                combined["emotional_tone"] = quant.get("mood", [])
        
        # Add GPS data
        if result.gps_result and result.gps_result.gps_coordinates:
            combined["analysis_methods"].append("gps")
            combined["gps_coordinates"] = result.gps_result.gps_coordinates
            combined["location_tag"] = result.gps_result.location_tag
            combined["geographic_metadata"] = {
                "altitude": result.gps_result.altitude,
                "heading": result.gps_result.heading,
                "timestamp": result.gps_result.timestamp.isoformat() if result.gps_result.timestamp else None,
            }
        
        # Cross-analysis insights
        combined["cross_analysis"] = self._generate_cross_analysis_insights(result)
        
        return combined
    
    def _generate_cross_analysis_insights(self, result: MultimodalResult) -> Dict[str, Any]:
        """Generate insights from combining different analysis methods."""
        insights = {}
        
        # CLIP + Vision correlation
        if result.clip_result and result.vision_result:
            insights["clip_vision_correlation"] = self._correlate_clip_vision(
                result.clip_result, result.vision_result
            )
        
        # Geographic context
        if result.gps_result and result.gps_result.gps_coordinates:
            insights["geographic_context"] = {
                "has_location": True,
                "coordinates": result.gps_result.gps_coordinates,
                "location_tag": result.gps_result.location_tag,
            }
            
            # If we have both location and content analysis
            if result.vision_result:
                insights["location_content_analysis"] = self._analyze_location_content(
                    result.gps_result, result.vision_result
                )
        
        # Temporal context
        if result.vision_result:
            insights["temporal_markers"] = self._extract_temporal_markers(
                result.vision_result
            )
        
        return insights
    
    def _correlate_clip_vision(
        self, 
        clip_result: CLIPResult, 
        vision_result: VisionAnalysisResult
    ) -> Dict[str, Any]:
        """Correlate CLIP similarities with Vision analysis."""
        correlation = {
            "method": "clip_vision_correlation",
            "confidence": "medium",
        }
        
        # Get top CLIP themes
        if clip_result.similarities:
            top_clip_themes = sorted(
                clip_result.similarities.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            correlation["top_clip_themes"] = top_clip_themes
        
        # Get vision objects/elements
        if vision_result.quantitative_format:
            quant = vision_result.quantitative_format
            correlation["vision_objects"] = quant.get("objects", [])
            correlation["vision_style"] = quant.get("style", [])
        
        # Simple keyword matching (could be enhanced with semantic similarity)
        if clip_result.similarities and vision_result.quantitative_format:
            matches = []
            for theme, score in clip_result.similarities.items():
                theme_words = theme.lower().split()
                for obj in vision_result.quantitative_format.get("objects", []):
                    if any(word in obj.lower() for word in theme_words):
                        matches.append({
                            "clip_theme": theme,
                            "clip_score": score,
                            "vision_object": obj,
                            "match_type": "keyword"
                        })
            correlation["thematic_matches"] = matches
        
        return correlation
    
    def _analyze_location_content(
        self,
        gps_result: GPSResult,
        vision_result: VisionAnalysisResult
    ) -> Dict[str, Any]:
        """Analyze relationship between location and visual content."""
        analysis = {
            "has_location": True,
            "coordinates": gps_result.gps_coordinates,
            "location_tag": gps_result.location_tag,
        }
        
        # Extract setting information from vision analysis
        if vision_result.quantitative_format:
            quant = vision_result.quantitative_format
            analysis["detected_setting"] = quant.get("setting", [])
            
            # Check for location consistency
            if gps_result.location_tag and "setting" in quant:
                setting_tokens = quant.get("setting", [])
                analysis["location_consistency"] = {
                    "gps_location": gps_result.location_tag,
                    "visual_setting": setting_tokens,
                    # Could add logic to check consistency
                }
        
        return analysis
    
    def _extract_temporal_markers(self, vision_result: VisionAnalysisResult) -> Dict[str, Any]:
        """Extract temporal information from vision analysis."""
        markers = {}
        
        if vision_result.quantitative_format:
            # Look for temporal tokens in various fields
            quant = vision_result.quantitative_format
            
            # Check for seasonal markers
            seasonal_terms = ["spring", "summer", "autumn", "winter", "seasonal"]
            for field in ["objects", "style", "mood"]:
                if field in quant:
                    seasonal_matches = [
                        token for token in quant[field]
                        if any(term in token.lower() for term in seasonal_terms)
                    ]
                    if seasonal_matches:
                        markers["seasonal_indicators"] = seasonal_matches
            
            # Check for time-of-day markers
            temporal_terms = ["morning", "afternoon", "evening", "night", "dawn", "dusk"]
            for field in ["objects", "style", "mood"]:
                if field in quant:
                    temporal_matches = [
                        token for token in quant[field]
                        if any(term in token.lower() for term in temporal_terms)
                    ]
                    if temporal_matches:
                        markers["time_indicators"] = temporal_matches
        
        return markers
    
    def analyze_batch(
        self,
        image_paths: List[str],
        clip_prompts: Optional[List[str]] = None,
        vision_template: Optional[str] = None,
        show_progress: bool = True,
    ) -> List[MultimodalResult]:
        """
        Analyze multiple images with multimodal analysis.
        
        Args:
            image_paths: List of image file paths
            clip_prompts: Text prompts for CLIP analysis
            vision_template: Custom template for Vision analysis
            show_progress: Whether to show progress
            
        Returns:
            List of MultimodalResult objects
        """
        results = []
        
        if show_progress:
            from tqdm import tqdm
            iterator = tqdm(image_paths, desc="Multimodal analysis")
        else:
            iterator = image_paths
        
        for image_path in iterator:
            try:
                result = self.analyze_image(
                    image_path, 
                    clip_prompts, 
                    vision_template
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze {image_path}: {e}")
                self.stats["errors"] += 1
        
        return results
    
    def analyze_folder(
        self,
        folder_path: str,
        clip_prompts: Optional[List[str]] = None,
        vision_template: Optional[str] = None,
        recursive: bool = False,
        show_progress: bool = True,
    ) -> List[MultimodalResult]:
        """
        Analyze all images in a folder with multimodal analysis.
        
        Args:
            folder_path: Path to folder containing images
            clip_prompts: Text prompts for CLIP analysis
            vision_template: Custom template for Vision analysis
            recursive: Whether to search recursively
            show_progress: Whether to show progress
            
        Returns:
            List of MultimodalResult objects
        """
        # Find image files
        image_paths = []
        valid_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
        
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
        
        return self.analyze_batch(
            image_paths,
            clip_prompts,
            vision_template,
            show_progress
        )
    
    def save_results(
        self,
        results: List[MultimodalResult],
        output_path: str,
        format: str = "json",
    ) -> None:
        """
        Save multimodal analysis results.
        
        Args:
            results: List of MultimodalResult objects
            output_path: Output file path
            format: Output format (json, csv)
        """
        if format.lower() == "json":
            self._save_json(results, output_path)
        elif format.lower() == "csv":
            self._save_csv(results, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _save_json(self, results: List[MultimodalResult], output_path: str) -> None:
        """Save results as JSON."""
        serializable_results = []
        
        for result in results:
            # Convert to serializable format
            serializable = {
                "filepath": result.filepath,
                "timestamp": result.timestamp.isoformat(),
                "combined_analysis": result.combined_analysis,
                "metadata": result.metadata,
            }
            
            # Add individual analysis results
            if result.clip_result:
                serializable["clip_analysis"] = {
                    "similarities": result.clip_result.similarities,
                    "metadata": result.clip_result.metadata,
                }
            
            if result.vision_result:
                serializable["vision_analysis"] = {
                    "qualitative_format": result.vision_result.qualitative_format,
                    "quantitative_format": result.vision_result.quantitative_format,
                    "error": result.vision_result.error,
                }
            
            if result.gps_result:
                serializable["gps_data"] = {
                    "coordinates": result.gps_result.gps_coordinates,
                    "location_tag": result.gps_result.location_tag,
                    "altitude": result.gps_result.altitude,
                    "heading": result.gps_result.heading,
                    "metadata": result.gps_result.metadata,
                }
            
            serializable_results.append(serializable)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(results)} multimodal results to {output_path}")
    
    def _save_csv(self, results: List[MultimodalResult], output_path: str) -> None:
        """Save results as CSV (flattened format)."""
        import pandas as pd
        
        rows = []
        for result in results:
            row = {
                "filepath": result.filepath,
                "timestamp": result.timestamp.isoformat(),
                "analysis_methods": ",".join(result.combined_analysis.get("analysis_methods", [])),
            }
            
            # Add CLIP data
            if result.clip_result:
                for prompt, score in result.clip_result.similarities.items():
                    row[f"clip_{prompt.replace(' ', '_')}"] = score
            
            # Add Vision data (simplified)
            if result.vision_result and not result.vision_result.error:
                if result.vision_result.quantitative_format:
                    quant = result.vision_result.quantitative_format
                    row["vision_objects"] = ",".join(quant.get("objects", []))
                    row["vision_style"] = ",".join(quant.get("style", []))
                    row["vision_colors"] = ",".join(quant.get("colors", []))
            
            # Add GPS data
            if result.gps_result and result.gps_result.gps_coordinates:
                row["latitude"] = result.gps_result.gps_coordinates[0]
                row["longitude"] = result.gps_result.gps_coordinates[1]
                row["location_tag"] = result.gps_result.location_tag
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        
        logger.info(f"Saved {len(results)} multimodal results to {output_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()
        
        # Add component stats
        if self.clip_analyzer:
            stats["clip_stats"] = self.clip_analyzer.get_stats()
        
        if self.vision_analyzer:
            stats["vision_stats"] = self.vision_analyzer.get_stats()
        
        if self.gps_extractor:
            stats["gps_stats"] = self.gps_extractor.get_stats()
        
        return stats