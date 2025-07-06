#!/usr/bin/env python3
"""
Run Japanese Poster Analysis with OpenAI Vision API

This script demonstrates the full multimodal analysis capabilities using both CLIP and OpenAI's GPT-4o model.
It requires an OpenAI API key to run.

Usage:
    export OPENAI_API_KEY=your_key_here
    python examples/run_poster_analysis_with_openai.py

Note: This will incur OpenAI API costs (~$0.15 per image with gpt-4o)
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from clip_humanists.core.config import load_config, save_config
    from clip_humanists.core.config import Config, ModelConfig, APIConfig, VisionAnalysisConfig
except ImportError as e:
    print(f"Error importing CLIP for Humanists modules: {e}")
    print("Please ensure the package is properly installed")
    sys.exit(1)

def setup_gpt4o_config():
    """Set up configuration to use GPT-4o for analysis."""
    
    # Create configuration with GPT-4o settings
    config = Config(
        model=ModelConfig(
            name="openai/clip-vit-base-patch32",
            batch_size=8,  # Smaller batch size for demo
            cache_embeddings=True
        ),
        apis=APIConfig(
            openai=ModelConfig(
                name="gpt-4o",  # Use the high-quality model
                max_concurrent=5,  # Limit concurrent requests
                rate_limit_delay=1.0  # Be conservative with rate limiting
            )
        ),
        vision_analysis=VisionAnalysisConfig(
            enable_qualitative=True,
            enable_quantitative=True,
            custom_template=None
        )
    )
    
    # Save the configuration
    config_path = Path("config/gpt4o_poster_analysis.yaml")
    config_path.parent.mkdir(exist_ok=True)
    save_config(config, str(config_path))
    
    print(f"✅ Configuration saved to {config_path}")
    return str(config_path)

async def main():
    """Run the poster analysis with GPT-4o."""
    
    print("🎌 Japanese Poster Analysis with GPT-4o")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OpenAI API key not found!")
        print("Please set your API key:")
        print("export OPENAI_API_KEY=your_key_here")
        print("\nNote: This analysis will use GPT-4o which costs ~$0.15 per image")
        return
    
    # Estimate cost
    poster_count = len(list(Path("data/japanese_example_posters").rglob("*.jpg")))
    limited_count = min(10, poster_count)  # Limit for demo
    estimated_cost = limited_count * 0.15
    
    print(f"📊 Found {poster_count} posters total")
    print(f"🔍 Will analyze {limited_count} posters for demo")
    print(f"💰 Estimated cost: ~${estimated_cost:.2f}")
    
    response = input("\nProceed with analysis? (y/N): ")
    if response.lower() != 'y':
        print("Analysis cancelled.")
        return
    
    # Set up configuration
    config_path = setup_gpt4o_config()
    
    # Import and run the analysis
    sys.path.insert(0, str(Path(__file__).parent))
    from japanese_poster_analysis_demo import JapaneseMannerPosterAnalyzer
    
    # Initialize with limited poster count for cost control
    analyzer = JapaneseMannerPosterAnalyzer()
    
    # Override to limit posters for demo
    original_get_files = analyzer.get_poster_files
    def limited_get_files():
        files = original_get_files()
        return files[:limited_count]  # Limit to 10 for demo
    analyzer.get_poster_files = limited_get_files
    
    try:
        print("\n🔬 Starting Full Multimodal Analysis...")
        print("This will use both CLIP and GPT-4o for comprehensive analysis")
        
        # Run the analysis
        analysis_data = await analyzer.run_comprehensive_analysis()
        
        # Analyze results
        stats = analyzer.analyze_results(analysis_data)
        
        # Create visualizations  
        fig_dir = analyzer.create_visualizations(analysis_data, stats)
        
        # Generate enhanced report
        report_path = analyzer.generate_markdown_report(analysis_data, stats, fig_dir)
        
        print("\n🎉 Full Multimodal Analysis Complete!")
        print("=" * 50)
        print(f"📊 Analyzed: {stats['total_posters']} posters")
        print(f"📈 Report: {report_path}")
        print(f"🔬 Analysis: CLIP + GPT-4o Vision API")
        print(f"💰 Approximate cost: ~${limited_count * 0.15:.2f}")
        
        if stats['top_themes']:
            print(f"🔍 Top finding: '{list(stats['top_themes'].keys())[0]}' (score: {list(stats['top_themes'].values())[0]:.3f})")
        
        print(f"\n📁 All outputs saved to: {analyzer.output_dir}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())