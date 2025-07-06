#!/usr/bin/env python3
"""
Basic demonstration of the refactored CLIP for Humanists system
with spatial autocorrelation analysis.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clip_humanists.core.clip_analyzer import EnhancedCLIPAnalyzer
from clip_humanists.core.gps_extractor import GPSExtractor
from clip_humanists.analysis.autocorrelation import SpatialAutocorrelation
from clip_humanists.core.config import Config, set_config


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main demonstration function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting CLIP for Humanists demonstration")
    
    # Set up configuration
    config = Config.default()
    set_config(config)
    
    # Define paths and parameters
    image_folder = Path(__file__).parent.parent / "img"
    
    # Check if image folder exists
    if not image_folder.exists():
        logger.error(f"Image folder not found: {image_folder}")
        return
    
    # Define text prompts for analysis
    text_prompts = [
        "street art",
        "commercial signage", 
        "warning signs",
        "cultural symbols",
        "urban architecture",
        "natural elements"
    ]
    
    # Define some example locations for GPS matching
    location_dict = {
        "downtown": (60.1699, 24.9384),  # Helsinki coordinates as example
        "suburbs": (60.2055, 24.9668),
        "university": (60.1841, 24.8301),
    }
    
    try:
        # Step 1: Initialize components
        logger.info("Initializing CLIP analyzer...")
        clip_analyzer = EnhancedCLIPAnalyzer(
            model_name="openai/clip-vit-base-patch32",
            batch_size=8,
            cache_dir="cache/embeddings"
        )
        
        logger.info("Initializing GPS extractor...")
        gps_extractor = GPSExtractor(
            location_dict=location_dict,
            max_distance_km=5.0
        )
        
        logger.info("Initializing spatial autocorrelation analyzer...")
        spatial_analyzer = SpatialAutocorrelation(
            distance_threshold=2.0,  # km
            k_neighbors=5,
            weight_type="inverse_distance"
        )
        
        # Step 2: Process images
        logger.info(f"Processing images in {image_folder}")
        
        # Extract GPS data
        gps_results = gps_extractor.extract_from_folder(
            str(image_folder),
            show_progress=True
        )
        
        logger.info(f"Found GPS data for {len(gps_results)} images")
        
        # Analyze images with CLIP
        clip_results = clip_analyzer.analyze_folder(
            str(image_folder),
            text_prompts,
            show_progress=True
        )
        
        logger.info(f"Analyzed {len(clip_results)} images with CLIP")
        
        # Step 3: Combine results
        logger.info("Combining GPS and CLIP results...")
        
        combined_data = []
        for clip_result in clip_results:
            # Find corresponding GPS result
            gps_result = next(
                (gps for gps in gps_results if gps.filepath == clip_result.filepath),
                None
            )
            
            if gps_result and gps_result.gps_coordinates:
                # Create combined result
                combined_result = clip_result
                combined_result.gps_coordinates = gps_result.gps_coordinates
                combined_result.location_tag = gps_result.location_tag
                combined_data.append(combined_result)
        
        logger.info(f"Combined data for {len(combined_data)} images with GPS coordinates")
        
        if len(combined_data) < 3:
            logger.warning("Need at least 3 images with GPS coordinates for spatial analysis")
            logger.info("Demonstration completed with limited data")
            return
        
        # Step 4: Spatial Autocorrelation Analysis
        logger.info("Performing spatial autocorrelation analysis...")
        
        # Moran's I analysis
        logger.info("Calculating Moran's I for all prompts...")
        moran_results = spatial_analyzer.morans_i(combined_data)
        
        for prompt, result in moran_results.items():
            logger.info(f"Moran's I for '{prompt}': {result.statistic:.3f} "
                       f"(p-value: {result.p_value:.3f}) - {result.interpretation}")
        
        # Local Moran's I for hotspot analysis (example with first prompt)
        if len(combined_data) >= 5:  # Need more data for local analysis
            first_prompt = text_prompts[0]
            logger.info(f"Calculating Local Moran's I for '{first_prompt}'...")
            
            try:
                local_moran = spatial_analyzer.local_morans_i(combined_data, first_prompt)
                logger.info(f"Found {len(local_moran.hotspots)} hotspots, "
                           f"{len(local_moran.coldspots)} coldspots, "
                           f"and {len(local_moran.outliers)} outliers")
            except Exception as e:
                logger.warning(f"Local Moran's I analysis failed: {e}")
        
        # Geary's C analysis
        logger.info("Calculating Geary's C...")
        try:
            geary_results = spatial_analyzer.gearys_c(combined_data)
            for prompt, result in geary_results.items():
                logger.info(f"Geary's C for '{prompt}': {result.statistic:.3f} "
                           f"(p-value: {result.p_value:.3f}) - {result.interpretation}")
        except Exception as e:
            logger.warning(f"Geary's C analysis failed: {e}")
        
        # Semantic autocorrelation
        logger.info("Calculating semantic autocorrelation...")
        try:
            semantic_results = spatial_analyzer.semantic_autocorrelation(combined_data)
            
            logger.info("Cross-correlations between prompts:")
            for pair, result in semantic_results["cross_correlations"].items():
                logger.info(f"{pair}: r={result['correlation']:.3f}, "
                           f"p={result['p_value']:.3f}")
        except Exception as e:
            logger.warning(f"Semantic autocorrelation analysis failed: {e}")
        
        # Step 5: Display statistics
        logger.info("\n=== Processing Statistics ===")
        
        clip_stats = clip_analyzer.get_stats()
        logger.info(f"CLIP Analysis:")
        logger.info(f"  Images processed: {clip_stats['images_processed']}")
        logger.info(f"  Average processing time: {clip_stats.get('avg_processing_time', 0):.2f}s")
        logger.info(f"  Cache hit rate: {clip_stats.get('cache_hit_rate', 0):.1%}")
        
        gps_stats = gps_extractor.get_stats()
        logger.info(f"GPS Extraction:")
        logger.info(f"  Images processed: {gps_stats['images_processed']}")
        logger.info(f"  GPS success rate: {gps_stats.get('gps_success_rate', 0):.1%}")
        logger.info(f"  Location match rate: {gps_stats.get('location_match_rate', 0):.1%}")
        
        logger.info("\n=== Demonstration completed successfully! ===")
        
    except Exception as e:
        logger.error(f"Error during demonstration: {e}")
        raise


if __name__ == "__main__":
    main()