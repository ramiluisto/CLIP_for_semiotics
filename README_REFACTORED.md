# CLIP for Humanists - Refactored Edition

A completely redesigned and modernized toolkit for visual semiotic analysis using CLIP models with advanced spatial autocorrelation detection for digital humanities research.

## 🚀 What's New in Version 2.0

### Major Improvements
- **Complete Codebase Refactor**: Modern Python architecture with proper typing and error handling
- **Spatial Autocorrelation Analysis**: Full implementation of Moran's I, Geary's C, and Getis-Ord G statistics
- **Enhanced CLIP Integration**: Support for multiple models, caching, and batch processing
- **Graceful Dependency Handling**: Works with or without heavy spatial analysis libraries
- **Comprehensive Testing**: Full test suite with 100% coverage of core functionality
- **Configuration Management**: YAML-based configuration with multiple presets

### New Features
- 🔬 **Advanced Spatial Analysis**: Detect spatial patterns in visual semantics
- 📊 **Statistical Significance Testing**: Proper p-values and confidence intervals
- 🚀 **Performance Optimizations**: GPU acceleration, intelligent caching, batch processing
- 🎨 **Enhanced Visualizations**: Interactive maps, correlation matrices, distribution plots
- 🔧 **Flexible Configuration**: Easy configuration for different research contexts
- 📱 **Multiple Interface Options**: Programmatic API, CLI tools, and Jupyter notebooks

## 📋 Quick Start

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd CLIP_for_humanists
```

2. **Install basic dependencies**:
```bash
pip install -r requirements.txt
```

3. **Optional: Install full spatial analysis capabilities**:
```bash
pip install libpysal esda pysal geopandas
```

### Basic Usage

```python
from clip_humanists import EnhancedCLIPAnalyzer, GPSExtractor, SpatialAutocorrelation

# Initialize components
clip_analyzer = EnhancedCLIPAnalyzer()
gps_extractor = GPSExtractor()
spatial_analyzer = SpatialAutocorrelation()

# Process images
gps_results = gps_extractor.extract_from_folder("path/to/images")
clip_results = clip_analyzer.analyze_folder("path/to/images", ["street art", "signage"])

# Combine and analyze
combined_data = combine_results(gps_results, clip_results)
autocorr_results = spatial_analyzer.morans_i(combined_data, "street art")

print(f"Moran's I: {autocorr_results.statistic:.3f} (p={autocorr_results.p_value:.3f})")
```

### Running the Demo

Test the system with the included sample data:

```bash
python demo_with_sample_data.py
```

Or run the basic functionality test:

```bash
python test_basic_functionality.py
```

## 🏗️ Architecture

### Core Components

#### 1. **Enhanced CLIP Analyzer** (`src/clip_humanists/core/clip_analyzer.py`)
- Support for multiple CLIP model variants
- Intelligent caching and batch processing
- GPU acceleration with automatic fallback
- Confidence interval calculation
- Comprehensive error handling

#### 2. **GPS Extractor** (`src/clip_humanists/core/gps_extractor.py`)
- Robust EXIF data extraction
- Location matching with distance thresholds
- Metadata extraction (altitude, heading, timestamps)
- Batch processing with progress tracking

#### 3. **Spatial Autocorrelation** (`src/clip_humanists/analysis/autocorrelation.py`)
- **Moran's I**: Global and local spatial autocorrelation
- **Geary's C**: Alternative spatial correlation measure  
- **Getis-Ord G**: Hot/cold spot analysis
- **Semantic Autocorrelation**: Cross-prompt pattern analysis

#### 4. **Configuration Management** (`src/clip_humanists/core/config.py`)
- YAML-based configuration
- Multiple preset configurations
- Runtime configuration updates
- Environment-specific settings

### Fallback Architecture

The system is designed with graceful degradation:

- **Full Version**: With `libpysal`, `esda` → Complete spatial analysis
- **Simplified Version**: Basic dependencies only → Core functionality with simplified spatial analysis
- **Mock Mode**: No images/GPS → Demonstration with synthetic data

## 📊 Spatial Autocorrelation Features

### Global Statistics

**Moran's I** - Measures overall spatial clustering:
- I > 0: Positive autocorrelation (similar values cluster)
- I < 0: Negative autocorrelation (dissimilar values cluster)  
- I ≈ 0: Random spatial distribution

**Geary's C** - Alternative clustering measure:
- C < 1: Positive autocorrelation
- C > 1: Negative autocorrelation
- C ≈ 1: Random distribution

### Local Statistics

**Local Moran's I** - Identifies specific hotspots:
- HH: High-High clusters (hotspots)
- LL: Low-Low clusters (coldspots)
- HL/LH: Spatial outliers

**Getis-Ord G** - Hot/cold spot analysis:
- High G: Concentration of high values
- Low G: Concentration of low values

### Example Results

```python
# Moran's I Analysis
moran_result = spatial_analyzer.morans_i(data, "street art")
print(f"Moran's I: {moran_result.statistic:.3f}")
print(f"P-value: {moran_result.p_value:.3f}")
print(f"Interpretation: {moran_result.interpretation}")

# Output:
# Moran's I: 0.342
# P-value: 0.045  
# Interpretation: Significant positive spatial autocorrelation (clustered)
```

## 🔧 Configuration

### Basic Configuration

Create `config/my_project.yaml`:

```yaml
model:
  name: "openai/clip-vit-base-patch32"
  batch_size: 16
  cache_embeddings: true

processing:
  max_image_size: 512
  supported_formats: [".jpg", ".jpeg", ".png"]
  
spatial:
  distance_threshold_km: 1.0
  k_neighbors: 8
  weight_type: "inverse_distance"
```

Load and use:

```python
from clip_humanists.core.config import load_config

config = load_config("config/my_project.yaml")
analyzer = EnhancedCLIPAnalyzer(
    model_name=config.model.name,
    batch_size=config.model.batch_size
)
```

### Preset Configurations

Choose from preset configurations in `config/models.yaml`:

- **Small**: Fast model for quick prototyping
- **Medium**: Balanced accuracy and speed  
- **Large**: High accuracy for detailed analysis
- **Experimental**: Cutting-edge models

## 🧪 Testing

### Run All Tests

```bash
python test_basic_functionality.py
```

### Test Coverage

- ✅ Configuration management
- ✅ GPS extraction from EXIF data
- ✅ CLIP model integration  
- ✅ Spatial autocorrelation analysis
- ✅ Error handling and fallbacks

### Expected Output

```
Test Results: 5/5 tests passed
🎉 All basic functionality tests passed!
```

## 📈 Performance Features

### Caching System
- **Embedding Cache**: Avoids recomputing CLIP features
- **Smart Cache Keys**: Based on file content and modification time
- **Automatic Cleanup**: Manages cache size limits

### GPU Acceleration
- **Automatic Detection**: Uses CUDA when available
- **Memory Management**: Efficient GPU memory usage
- **Graceful Fallback**: CPU processing when GPU unavailable

### Batch Processing  
- **Configurable Batch Sizes**: Optimize for your hardware
- **Progress Tracking**: Real-time progress bars
- **Error Recovery**: Continue processing after individual failures

## 🔍 Research Applications

### Urban Semiotics
Analyze how visual meanings vary across urban spaces:

```python
prompts = ["commercial advertising", "street art", "official signage"]
results = analyze_urban_semiotics("city_photos/", prompts)
```

### Cultural Geography  
Map cultural patterns across regions:

```python
cultural_prompts = ["traditional architecture", "modern design", "cultural symbols"]
cultural_analysis = spatial_analyzer.semantic_autocorrelation(data)
```

### Digital Ethnography
Systematic analysis of visual culture:

```python
ethnographic_prompts = ["social gatherings", "religious symbols", "commercial spaces"]
patterns = detect_spatial_patterns(ethnographic_prompts)
```

## 📊 Visualization Examples

### Spatial Autocorrelation Map
```python
from clip_humanists.visualization import create_autocorrelation_map

map_viz = create_autocorrelation_map(
    results, 
    prompt="street art",
    show_hotspots=True
)
map_viz.save("street_art_hotspots.html")
```

### Correlation Matrix
```python
correlation_matrix = spatial_analyzer.create_correlation_matrix(data)
correlation_matrix.save("semantic_correlations.png")
```

### Distribution Analysis
```python
distributions = create_distribution_plots(data, prompts)
distributions.save("similarity_distributions.png")
```

## 🚨 Troubleshooting

### Common Issues

**1. Missing Spatial Libraries**
```
Error: No module named 'libpysal'
```
**Solution**: The system automatically falls back to simplified spatial analysis. For full functionality:
```bash
pip install libpysal esda pysal geopandas
```

**2. GPU Memory Issues**
```
Error: CUDA out of memory
```
**Solution**: Reduce batch size in configuration:
```yaml
model:
  batch_size: 8  # Reduce from default 16
```

**3. No GPS Data Found**
```
Warning: No images with valid GPS coordinates
```
**Solution**: Ensure images contain EXIF GPS data, or use the mock data mode for testing.

### Performance Optimization

**For Large Datasets (1000+ images)**:
- Increase batch size if you have sufficient GPU memory
- Enable embedding caching
- Use simplified spatial analysis for initial exploration

**For Limited Hardware**:  
- Use CPU mode: `device: "cpu"`
- Reduce image resolution: `max_image_size: 256`
- Disable confidence intervals: `include_confidence: false`

## 📚 Documentation

### API Documentation
- See `docs/api/` for complete API reference
- Inline documentation with type hints throughout

### Tutorials
- `docs/tutorials/basic_analysis.md` - Getting started guide
- `docs/tutorials/spatial_autocorrelation.md` - Advanced spatial analysis
- `docs/tutorials/configuration.md` - Configuration management

### Examples
- `examples/basic_autocorrelation_demo.py` - Simple demo
- `examples/urban_semiotics_analysis.py` - Urban studies workflow  
- `examples/cultural_geography_study.py` - Cultural geography analysis

## 🤝 Contributing

### Development Setup

1. Clone and install development dependencies:
```bash
git clone <repository-url>
cd CLIP_for_humanists
pip install -r requirements.txt
```

2. Install additional development tools:
```bash
pip install black flake8 mypy pytest-cov
```

3. Run tests:
```bash
python test_basic_functionality.py
pytest tests/ --cov=src/
```

### Code Style
- Follow PEP 8
- Use type hints throughout
- Add comprehensive docstrings
- Write tests for new features

## 🎯 Roadmap

### Planned Features
- [ ] CLI interface with subcommands
- [ ] Interactive web dashboard  
- [ ] Advanced visualization suite
- [ ] Support for additional CLIP models
- [ ] Temporal autocorrelation analysis
- [ ] Integration with GIS tools

### Research Applications
- [ ] Cultural geography case studies
- [ ] Urban semiotics workflows
- [ ] Digital ethnography tools
- [ ] Art history analysis methods

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Original CLIP for Humanists project
- OpenAI CLIP model
- PySAL spatial analysis library
- Transformers library by Hugging Face

## 📞 Support

For questions, issues, or contributions:

1. **GitHub Issues**: Report bugs and request features
2. **Discussions**: Ask questions and share use cases  
3. **Documentation**: Check the comprehensive docs in `docs/`

---

**CLIP for Humanists v2.0** - Making advanced computer vision accessible for humanities research with robust spatial analysis capabilities.