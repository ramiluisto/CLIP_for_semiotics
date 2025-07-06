# CLIP for Humanists - Project Structure

## 📁 Clean Project Organization

```
CLIP_for_humanists/
├── 📄 README.md                    # Main documentation
├── 📄 QUICK_START.md               # 5-minute getting started guide
├── 📄 CLAUDE.md                    # Original project context
├── 📄 refactor_plan.md             # Detailed refactor plan
├── 📄 SUMMARY_OF_REFACTOR.md       # What was accomplished
├── 📄 requirements.txt             # Python dependencies
├── 📄 setup.py                     # Package installation
├── 📄 pyproject.toml              # Modern Python package config
├── 📄 MANIFEST.in                 # Package data inclusion
├── 📄 .gitignore                  # Git ignore patterns
├── 📄 pytest.ini                 # Test configuration
│
├── 📁 src/                        # Source code
│   └── 📁 clip_humanists/
│       ├── 📄 __init__.py         # Package initialization
│       ├── 📁 core/               # Core functionality
│       │   ├── 📄 __init__.py
│       │   ├── 📄 clip_analyzer.py     # Enhanced CLIP analysis
│       │   ├── 📄 gps_extractor.py     # GPS data extraction
│       │   └── 📄 config.py            # Configuration management
│       └── 📁 analysis/           # Spatial analysis
│           ├── 📄 __init__.py
│           ├── 📄 autocorrelation.py        # Full spatial analysis
│           └── 📄 autocorrelation_simple.py # Simplified fallback
│
├── 📁 config/                     # Configuration files
│   ├── 📄 default.yaml           # Default settings
│   └── 📄 models.yaml            # Model presets
│
├── 📁 examples/                   # Usage examples
│   ├── 📄 demo_with_sample_data.py      # Complete demo
│   └── 📄 basic_autocorrelation_demo.py # Basic example
│
├── 📁 tests/                      # Test suite
│   ├── 📄 __init__.py
│   └── 📄 test_basic_functionality.py   # Core functionality tests
│
├── 📁 img/                        # Sample images with GPS data
│   ├── 📄 IMG20231116100742.jpg
│   ├── 📄 IMG20240325100746.jpg
│   └── 📄 IMG20240325100812.jpg
│
├── 📁 output/                     # Generated results
│   └── 📄 .gitkeep               # Keeps directory in git
│
└── 📄 CLIP_for_Humanists.ipynb   # Original Jupyter notebook
```

## 🗂️ Files Removed During Cleanup

### Duplicate and Unnecessary Files
- ❌ `clip_for_humanists.egg-info/` - Auto-generated package info
- ❌ `draft_version/` - Old draft code
- ❌ `example_img/` - Duplicate of `img/`
- ❌ `small_img_temp/` - Temporary files
- ❌ `result_images/` - Old result files
- ❌ `plan_for_o3.md` - Outdated planning document
- ❌ `resize_images.py` - Utility script
- ❌ `src/*.py` - Old source files in wrong location
- ❌ `tests/test_*.py` - Outdated test files
- ❌ `COLAB_INSTRUCTIONS.md` - Outdated instructions
- ❌ `RUNNING_LOCALLY.md` - Outdated instructions

### Consolidated Files
- ✅ `README_REFACTORED.md` → `README.md` (replaced main README)
- ✅ Moved demos to `examples/`
- ✅ Moved tests to `tests/`

## 🏗️ Key Components

### Core Modules

**🧠 Enhanced CLIP Analyzer** (`src/clip_humanists/core/clip_analyzer.py`)
- Multiple CLIP model support
- Intelligent caching system
- GPU acceleration with CPU fallback
- Batch processing optimization
- Comprehensive error handling

**🗺️ GPS Extractor** (`src/clip_humanists/core/gps_extractor.py`)
- Robust EXIF data extraction
- Location matching with distance thresholds
- Metadata extraction (timestamps, altitude, heading)
- Statistical reporting and clustering

**⚙️ Configuration Management** (`src/clip_humanists/core/config.py`)
- YAML-based configuration system
- Multiple preset configurations
- Runtime configuration updates
- Type-safe dataclass-based configuration

### Analysis Modules

**📊 Spatial Autocorrelation** (`src/clip_humanists/analysis/`)
- **Full version**: Complete spatial analysis with libpysal/esda
- **Simplified version**: Basic analysis without heavy dependencies
- Moran's I, Geary's C, Getis-Ord G statistics
- Local hotspot detection
- Cross-prompt semantic analysis

### Configuration

**📋 Default Config** (`config/default.yaml`)
- Sensible defaults for all parameters
- Model selection and optimization settings
- Spatial analysis parameters
- Visualization preferences

**🎛️ Model Presets** (`config/models.yaml`)
- Small, medium, large model configurations
- Prompt templates for different research areas
- Location sets for different geographic regions

## 🎯 Usage Patterns

### Quick Testing
```bash
python tests/test_basic_functionality.py
```

### Full Demonstration
```bash
python examples/demo_with_sample_data.py
```

### Custom Analysis
```python
from clip_humanists import EnhancedCLIPAnalyzer, GPSExtractor, SpatialAutocorrelation
# See examples/ for complete workflows
```

## 🔄 Development Workflow

### Adding New Features
1. Implement in appropriate module under `src/clip_humanists/`
2. Add tests in `tests/`
3. Add example usage in `examples/`
4. Update configuration if needed

### Running Tests
```bash
python tests/test_basic_functionality.py
```

### Package Installation
```bash
pip install -e .  # Development installation
```

## 📦 Package Distribution

The project is now properly organized for distribution:
- ✅ Modern `pyproject.toml` configuration
- ✅ Traditional `setup.py` for compatibility
- ✅ Proper package structure under `src/`
- ✅ Include package data (config files)
- ✅ Console script entry points
- ✅ Comprehensive dependency management

This clean structure makes the project:
- **Easy to install**: Standard Python packaging
- **Easy to use**: Clear examples and documentation
- **Easy to extend**: Modular architecture
- **Easy to maintain**: Organized codebase with tests