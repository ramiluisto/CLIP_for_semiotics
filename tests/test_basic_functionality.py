#!/usr/bin/env python3
"""
Basic functionality test for the refactored CLIP for Humanists system.
This script tests core components without requiring heavy dependencies.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test if all core modules can be imported."""
    print("Testing imports...")
    
    try:
        from clip_humanists.core.config import Config, get_config, set_config
        print("✓ Config module imported successfully")
        
        from clip_humanists.core.gps_extractor import GPSExtractor, GPSResult
        print("✓ GPS extractor imported successfully")
        
        # Test simplified autocorrelation import
        try:
            from clip_humanists.analysis.autocorrelation_simple import SimpleSpatialAutocorrelation
            print("✓ Simplified autocorrelation imported successfully")
        except ImportError as e:
            print(f"⚠ Simplified autocorrelation import failed: {e}")
        
        # Test config creation
        config = Config.default()
        print(f"✓ Default config created: model={config.model.name}")
        
        # Test GPS extractor initialization
        gps_extractor = GPSExtractor()
        print("✓ GPS extractor initialized")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_config():
    """Test configuration system."""
    print("\nTesting configuration system...")
    
    try:
        from clip_humanists.core.config import Config
        
        # Test default config
        config = Config.default()
        print(f"✓ Default config: {config.model.name}")
        
        # Test config modification
        config.model.batch_size = 8
        print(f"✓ Config modified: batch_size={config.model.batch_size}")
        
        # Test YAML save/load
        config_path = "test_config.yaml"
        config.to_yaml(config_path)
        print("✓ Config saved to YAML")
        
        loaded_config = Config.from_yaml(config_path)
        print(f"✓ Config loaded from YAML: batch_size={loaded_config.model.batch_size}")
        
        # Cleanup
        os.remove(config_path)
        print("✓ Test config file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ Config test error: {e}")
        return False

def test_gps_extractor():
    """Test GPS extractor with sample images."""
    print("\nTesting GPS extractor...")
    
    try:
        from clip_humanists.core.gps_extractor import GPSExtractor
        
        # Test initialization
        location_dict = {
            "test_location": (60.1699, 24.9384)
        }
        
        gps_extractor = GPSExtractor(
            location_dict=location_dict,
            max_distance_km=5.0
        )
        print("✓ GPS extractor initialized with location dictionary")
        
        # Test with sample image folder
        img_folder = Path(__file__).parent.parent / "img"
        if img_folder.exists():
            print(f"Testing with images in {img_folder}")
            results = gps_extractor.extract_from_folder(str(img_folder), show_progress=False)
            print(f"✓ Processed {len(results)} images")
            
            # Show statistics
            stats = gps_extractor.get_stats()
            print(f"✓ GPS found in {stats['gps_found']}/{stats['images_processed']} images")
            
        else:
            print("ⓘ No img folder found, skipping image processing test")
        
        return True
        
    except Exception as e:
        print(f"✗ GPS extractor test error: {e}")
        return False

def test_clip_analyzer_imports():
    """Test CLIP analyzer imports (without loading models)."""
    print("\nTesting CLIP analyzer imports...")
    
    try:
        from clip_humanists.core.clip_analyzer import EnhancedCLIPAnalyzer, CLIPResult
        print("✓ CLIP analyzer classes imported successfully")
        
        # Test result dataclass
        result = CLIPResult(
            filepath="test.jpg",
            similarities={"test_prompt": 0.8}
        )
        print(f"✓ CLIPResult created: {result.filepath}")
        
        return True
        
    except ImportError as e:
        print(f"✗ CLIP analyzer import error: {e}")
        print("  This might be due to missing PyTorch/Transformers")
        return False
    except Exception as e:
        print(f"✗ CLIP analyzer test error: {e}")
        return False

def test_autocorrelation_imports():
    """Test spatial autocorrelation imports."""
    print("\nTesting spatial autocorrelation imports...")
    
    try:
        # Try simplified version first
        from clip_humanists.analysis.autocorrelation_simple import (
            SimpleSpatialAutocorrelation, SimpleMoranResult
        )
        print("✓ Simplified spatial autocorrelation classes imported successfully")
        
        # Test result dataclass
        moran_result = SimpleMoranResult(
            statistic=0.5,
            expected_value=0.0,
            variance=0.1,
            z_score=1.5,
            p_value=0.05,
            interpretation="Test result"
        )
        print(f"✓ SimpleMoranResult created: {moran_result.interpretation}")
        
        # Try to import full version
        try:
            from clip_humanists.analysis.autocorrelation import (
                SpatialAutocorrelation, MoranResult, LocalMoranResult, GearyResult
            )
            print("✓ Full spatial autocorrelation classes also available")
        except ImportError:
            print("ⓘ Full spatial autocorrelation not available (missing libpysal/esda)")
        
        return True
        
    except ImportError as e:
        print(f"✗ Autocorrelation import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Autocorrelation test error: {e}")
        return False

def main():
    """Run all basic functionality tests."""
    print("CLIP for Humanists - Basic Functionality Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_gps_extractor,
        test_clip_analyzer_imports,
        test_autocorrelation_imports,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic functionality tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check dependencies and installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())