#!/usr/bin/env python3
"""
Demonstration of the integrated CLIP + OpenAI Vision multimodal analysis system.
This example shows how to combine CLIP similarity analysis with detailed
OpenAI Vision content analysis for comprehensive image understanding.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clip_humanists.analysis.multimodal_content import MultimodalContentAnalyzer
from clip_humanists.core.clip_analyzer import EnhancedCLIPAnalyzer
from clip_humanists.core.gps_extractor import GPSExtractor
from clip_humanists.core.config import Config, set_config


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def check_openai_key():
    """Check if OpenAI API key is available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OpenAI API key not found.")
        print("   To enable Vision analysis, set OPENAI_API_KEY environment variable")
        print("   For now, running with CLIP-only analysis")
        return False
    print("✓ OpenAI API key found - Vision analysis enabled")
    return True


def create_mock_multimodal_demo():
    """Create a mock demo when OpenAI API is not available."""
    from clip_humanists.core.clip_analyzer import CLIPResult
    from clip_humanists.apis.openai_vision import VisionAnalysisResult
    from clip_humanists.analysis.multimodal_content import MultimodalResult
    from datetime import datetime
    
    print("\n📊 Mock Multimodal Analysis Demo")
    print("=" * 50)
    
    # Create mock CLIP result
    mock_clip_result = CLIPResult(
        filepath="mock_image.jpg",
        similarities={
            "street art": 0.75,
            "urban architecture": 0.45,
            "commercial signage": 0.62,
            "cultural symbols": 0.38
        }
    )
    
    # Create mock Vision result
    mock_vision_result = VisionAnalysisResult(
        filepath="mock_image.jpg",
        model_name="gpt-4o-mini",
        timestamp=datetime.now(),
        qualitative_format={
            "description": "A vibrant street art mural depicting cultural symbols and urban life",
            "visual_elements": "Bold colors, geometric patterns, contemporary graffiti style",
            "cultural_context": "Modern urban expression with traditional motifs",
            "narrative": "The image conveys a story of cultural fusion in urban spaces"
        },
        quantitative_format={
            "objects": ["mural", "wall", "text", "symbols"],
            "colors": ["red", "blue", "yellow", "black"],
            "style": ["street_art", "contemporary", "geometric"],
            "mood": ["vibrant", "energetic", "cultural"],
            "setting": ["urban", "outdoor", "street"]
        }
    )
    
    # Create combined result
    mock_multimodal_result = MultimodalResult(
        filepath="mock_image.jpg",
        timestamp=datetime.now(),
        clip_result=mock_clip_result,
        vision_result=mock_vision_result
    )
    
    # Demonstrate analysis correlation
    print("🎨 CLIP Analysis Results:")
    for prompt, score in mock_clip_result.similarities.items():
        print(f"  {prompt}: {score:.3f}")
    
    print("\n🔍 Vision Analysis Results:")
    print(f"  Description: {mock_vision_result.qualitative_format['description']}")
    print(f"  Objects: {', '.join(mock_vision_result.quantitative_format['objects'])}")
    print(f"  Style: {', '.join(mock_vision_result.quantitative_format['style'])}")
    print(f"  Colors: {', '.join(mock_vision_result.quantitative_format['colors'])}")
    
    print("\n🔗 Cross-Analysis Insights:")
    print("  Top CLIP theme: street art (0.75) ↔ Vision style: street_art")
    print("  CLIP 'urban architecture' (0.45) ↔ Vision setting: urban")
    print("  CLIP 'cultural symbols' (0.38) ↔ Vision objects: symbols")
    
    print("\n💡 This demonstrates how CLIP embeddings complement Vision analysis:")
    print("  • CLIP provides quantitative similarity scores for research queries")
    print("  • Vision provides rich qualitative context and structured tokens")
    print("  • Combined analysis enables both statistical analysis and cultural interpretation")


def main():
    """Main demonstration function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🔬 CLIP for Humanists: Multimodal Analysis Demo")
    print("=" * 60)
    
    # Check if OpenAI API is available
    has_openai = check_openai_key()
    
    if not has_openai:
        create_mock_multimodal_demo()
        return 0
    
    # Set up configuration
    config = Config.default()
    config.model.batch_size = 4  # Small batch for demo
    set_config(config)
    
    # Define paths and parameters
    image_folder = Path(__file__).parent.parent / "img"
    
    # Define analysis parameters
    clip_prompts = [
        "street art",
        "commercial signage",
        "urban architecture", 
        "natural elements",
        "cultural symbols"
    ]
    
    # Custom Vision analysis template for cultural analysis
    vision_template = """
You are a specialist in visual culture and semiotics. Analyze this image and provide structured analysis in JSON format.

Reply with one JSON object containing:
{
  "qualitative_format": {
    "description": "Detailed description of the image content and composition",
    "cultural_context": "Cultural and semiotic interpretation of visual elements",
    "visual_strategies": "Analysis of visual communication techniques used",
    "narrative": "The story or message conveyed by the image"
  },
  "quantitative_format": {
    "objects": ["list", "of", "identified", "objects"],
    "visual_style": ["artistic", "style", "tokens"],
    "cultural_markers": ["cultural", "reference", "tokens"],
    "colors": ["dominant", "colors"],
    "setting": ["location", "context", "markers"],
    "mood": ["emotional", "tone", "indicators"]
  }
}

Use lowercase snake_case for quantitative tokens. Focus on cultural and semiotic elements.
"""
    
    try:
        print("\n1. Initializing Multimodal Content Analyzer...")
        
        # Initialize individual components
        clip_analyzer = EnhancedCLIPAnalyzer(
            model_name="openai/clip-vit-base-patch32",
            batch_size=4,
            cache_dir="cache/embeddings"
        )
        
        try:
            from clip_humanists.apis.openai_vision import OpenAIVisionAnalyzer
            vision_analyzer = OpenAIVisionAnalyzer(
                model_name="gpt-4o-mini",
                max_concurrent=2,  # Conservative for demo
                rate_limit_delay=1.0
            )
            vision_enabled = True
        except ImportError:
            print("⚠️  OpenAI package not available - running CLIP-only analysis")
            vision_analyzer = None
            vision_enabled = False
        except ValueError as e:
            print(f"⚠️  {e}")
            print("   Running CLIP-only analysis")
            vision_analyzer = None
            vision_enabled = False
        
        gps_extractor = GPSExtractor()
        
        # Initialize multimodal analyzer
        multimodal_analyzer = MultimodalContentAnalyzer(
            clip_analyzer=clip_analyzer,
            vision_analyzer=vision_analyzer,
            gps_extractor=gps_extractor,
            enable_clip=True,
            enable_vision=vision_enabled,
            enable_gps=True
        )
        
        print("✓ Multimodal analyzer initialized")
        
        print("\n2. Processing Sample Images...")
        
        if not image_folder.exists():
            print(f"⚠️  Image folder not found: {image_folder}")
            print("   Creating mock analysis demonstration instead")
            create_mock_multimodal_demo()
            return 0
        
        # Analyze a small subset for demo (first 2 images)
        import os
        image_files = [
            f for f in os.listdir(image_folder) 
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ][:2]  # Limit to 2 images for demo
        
        if not image_files:
            print("⚠️  No image files found")
            create_mock_multimodal_demo()
            return 0
        
        image_paths = [str(image_folder / f) for f in image_files]
        
        print(f"Analyzing {len(image_paths)} images...")
        
        # Perform multimodal analysis
        results = multimodal_analyzer.analyze_batch(
            image_paths,
            clip_prompts=clip_prompts,
            vision_template=vision_template if vision_enabled else None,
            show_progress=True
        )
        
        print(f"\n3. Analysis Results ({len(results)} images processed)")
        print("-" * 50)
        
        for i, result in enumerate(results):
            print(f"\n📸 Image {i+1}: {Path(result.filepath).name}")
            
            # CLIP Results
            if result.clip_result:
                print("  🎯 CLIP Similarity Scores:")
                sorted_similarities = sorted(
                    result.clip_result.similarities.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                for prompt, score in sorted_similarities:
                    print(f"    {prompt}: {score:.3f}")
            
            # Vision Results
            if result.vision_result and not result.vision_result.error:
                print("  🔍 Vision Analysis:")
                qual = result.vision_result.qualitative_format
                quant = result.vision_result.quantitative_format
                
                if "description" in qual:
                    desc = qual["description"][:100] + "..." if len(qual["description"]) > 100 else qual["description"]
                    print(f"    Description: {desc}")
                
                if "objects" in quant:
                    print(f"    Objects: {', '.join(quant['objects'][:5])}")
                
                if "visual_style" in quant:
                    print(f"    Style: {', '.join(quant['visual_style'][:3])}")
            
            elif result.vision_result and result.vision_result.error:
                print(f"  ⚠️  Vision analysis error: {result.vision_result.error}")
            
            # GPS Results
            if result.gps_result and result.gps_result.gps_coordinates:
                coords = result.gps_result.gps_coordinates
                print(f"  📍 GPS: ({coords[0]:.4f}, {coords[1]:.4f})")
                if result.gps_result.location_tag:
                    print(f"    Location: {result.gps_result.location_tag}")
            
            # Combined Analysis Insights
            if result.combined_analysis.get("cross_analysis"):
                cross = result.combined_analysis["cross_analysis"]
                if "clip_vision_correlation" in cross:
                    corr = cross["clip_vision_correlation"]
                    matches = corr.get("thematic_matches", [])
                    if matches:
                        print("  🔗 CLIP-Vision Correlations:")
                        for match in matches[:2]:  # Show top 2 matches
                            print(f"    {match['clip_theme']} ({match['clip_score']:.3f}) ↔ {match['vision_object']}")
        
        print("\n4. Summary Statistics")
        print("-" * 50)
        
        stats = multimodal_analyzer.get_stats()
        print(f"Images processed: {stats['images_processed']}")
        print(f"CLIP analyses: {stats['clip_analyses']}")
        print(f"Vision analyses: {stats['vision_analyses']}")
        print(f"GPS extractions: {stats['gps_extractions']}")
        print(f"Combined analyses: {stats['combined_analyses']}")
        print(f"Errors: {stats['errors']}")
        
        # Component stats
        if "clip_stats" in stats:
            clip_stats = stats["clip_stats"]
            print(f"\nCLIP Statistics:")
            print(f"  Average processing time: {clip_stats.get('avg_processing_time', 0):.2f}s")
            print(f"  Cache hit rate: {clip_stats.get('cache_hit_rate', 0):.1%}")
        
        if "vision_stats" in stats and vision_enabled:
            vision_stats = stats["vision_stats"]
            print(f"\nVision API Statistics:")
            print(f"  Success rate: {vision_stats.get('success_rate', 0):.1%}")
            print(f"  Total API calls: {vision_stats.get('total_api_calls', 0)}")
            
            if vision_stats.get('total_api_calls', 0) > 0:
                cost_estimate = vision_analyzer.estimate_cost(vision_stats['total_api_calls'])
                print(f"  Estimated cost: ${cost_estimate['estimated_cost_usd']:.4f}")
        
        print("\n5. Research Applications")
        print("-" * 50)
        print("✓ Cultural Visual Studies: Combine quantitative similarity with qualitative interpretation")
        print("✓ Digital Humanities: Scale up archival analysis with AI-assisted cultural context")
        print("✓ Urban Semiotics: Analyze spatial patterns in visual communication")
        print("✓ Cross-Cultural Research: Compare visual meanings across different contexts")
        print("✓ Temporal Analysis: Track evolution of visual culture over time")
        
        print("\n🎉 Multimodal analysis demonstration completed!")
        
        if vision_enabled:
            print("\n💡 Next Steps:")
            print("  • Customize vision analysis templates for your research domain")
            print("  • Use temporal analysis for longitudinal studies")
            print("  • Combine with spatial autocorrelation for geographic patterns")
            print("  • Export results for statistical analysis and visualization")
        else:
            print("\n💡 To enable full multimodal analysis:")
            print("  1. Install OpenAI package: pip install openai")
            print("  2. Set OpenAI API key: export OPENAI_API_KEY=your_key_here")
            print("  3. Re-run this demo for complete functionality")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())