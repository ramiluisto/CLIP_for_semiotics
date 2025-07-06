# CLIP for Humanists - Comprehensive Multimodal Analysis Platform

A complete toolkit for visual semiotic analysis using CLIP models, spatial autocorrelation analysis, and multimodal content analysis for digital humanities research.

## 🚀 What's New in Version 2.0

### Major Capabilities
- **🔬 Advanced Multimodal Analysis**: Combines CLIP embeddings with OpenAI Vision API for comprehensive content analysis
- **📊 Spatial Autocorrelation**: Full implementation of Moran's I, Geary's C, and Getis-Ord G statistics
- **🎨 Enhanced CLIP Integration**: Support for multiple models, caching, and batch processing
- **🌍 GPS & Geospatial Analysis**: Extract and analyze location-based patterns in visual data
- **📈 Cross-Analysis Correlation**: Automatic correlation between different analysis methods
- **🔧 Graceful Degradation**: Works with or without optional dependencies (OpenAI API, spatial libraries)

### Research Applications
- **Cultural Visual Studies**: Japanese manner posters, propaganda, advertising campaigns
- **Digital Humanities**: Large-scale archival analysis with cultural context
- **Urban Semiotics**: Signage evolution and visual communication patterns
- **Social Media Studies**: Cultural patterns in visual communication over time
- **Museum Collections**: Systematic analysis of visual art with interpretation

## 📋 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd CLIP_for_humanists

# Install core dependencies
pip install -r requirements.txt

# Optional: Install full spatial analysis capabilities
pip install libpysal esda pysal geopandas

# Optional: For OpenAI Vision API (multimodal analysis)
pip install openai python-dotenv
export OPENAI_API_KEY=your_key_here
```

### 2. Test the Installation

```bash
# Run the comprehensive test suite
python tests/test_basic_functionality.py

# Expected output: "🎉 All basic functionality tests passed!"
```

### 3. Try the Demos

```bash
# Basic CLIP and spatial analysis
python examples/demo_with_sample_data.py

# Comprehensive multimodal analysis (requires OpenAI API key)
python examples/multimodal_analysis_demo.py
```

## 🏗️ Core Architecture

### Analysis Pipeline

```python
# Basic Analysis Pipeline
GPS Data → CLIP Analysis → Spatial Autocorrelation

# Enhanced Multimodal Pipeline  
GPS Data → CLIP Analysis → OpenAI Vision Analysis → Cross-Analysis Correlation
        → Spatial Autocorrelation → Comprehensive Insights
```

### Core Components

#### 1. **Enhanced CLIP Analyzer** (`src/clip_humanists/core/clip_analyzer.py`)
- Multiple CLIP model variants (ViT-B/32, ViT-B/16, ViT-L/14)
- Intelligent caching and batch processing
- GPU acceleration with automatic fallback
- Confidence interval calculation

#### 2. **GPS & Geospatial Extractor** (`src/clip_humanists/core/gps_extractor.py`)
- Robust EXIF data extraction
- Location matching with distance thresholds
- Temporal metadata extraction
- Statistical reporting and clustering

#### 3. **Spatial Autocorrelation Suite** (`src/clip_humanists/analysis/`)
- **Moran's I**: Global and local spatial autocorrelation
- **Geary's C**: Alternative spatial correlation measure
- **Getis-Ord G**: Hot/cold spot analysis
- **Semantic Autocorrelation**: Cross-prompt pattern analysis

#### 4. **Multimodal Content Analyzer** (`src/clip_humanists/analysis/multimodal_content.py`)
- OpenAI Vision API integration
- Dual-format analysis (qualitative + quantitative)
- Cultural context analysis
- Cross-analysis correlation with CLIP results

#### 5. **OpenAI Vision Integration** (`src/clip_humanists/apis/openai_vision.py`)
- Advanced image content analysis using GPT-4o models
- Rate limiting and error handling
- Structured output formats
- Statistical framework for analysis

### Configuration Management (`src/clip_humanists/core/config.py`)
- YAML-based configuration system
- Multiple preset configurations
- Optional dependency handling
- Runtime configuration updates

## 🔬 Analysis Capabilities

### 1. **CLIP Similarity Analysis**
```python
from clip_humanists import EnhancedCLIPAnalyzer

clip_analyzer = EnhancedCLIPAnalyzer()
results = clip_analyzer.analyze_folder(
    "path/to/images", 
    ["street art", "signage", "architecture"]
)
```

### 2. **Spatial Autocorrelation Analysis**
```python
from clip_humanists import SpatialAutocorrelation

spatial_analyzer = SpatialAutocorrelation()
moran_results = spatial_analyzer.morans_i(combined_data, "street_art")
print(f"Moran's I: {moran_results.statistic:.3f} (p={moran_results.p_value:.3f})")
```

### 3. **Multimodal Content Analysis**
```python
from clip_humanists import MultimodalContentAnalyzer

# Requires OpenAI API key
multimodal_analyzer = MultimodalContentAnalyzer(
    enable_clip=True,      # Quantitative similarity analysis
    enable_vision=True,    # Qualitative content analysis
    enable_gps=True        # Spatial data extraction
)

results = multimodal_analyzer.analyze_folder(
    "path/to/images",
    clip_prompts=["street art", "signage", "architecture"],
    vision_template=custom_cultural_analysis_template
)
```

### 4. **Cross-Analysis Correlation**
```python
# Automatic correlation between CLIP and Vision API results
correlations = multimodal_analyzer.get_cross_analysis_correlations(results)
```

## 📊 Understanding Results

### Spatial Autocorrelation Interpretation
- **Moran's I > 0**: Positive autocorrelation (similar values cluster together)
- **Moran's I < 0**: Negative autocorrelation (dissimilar values cluster together)
- **Moran's I ≈ 0**: Random spatial distribution
- **p-value < 0.05**: Statistically significant spatial pattern

### Example Output
```
=== CLIP Analysis ===
Prompt: 'street art'
  Mean Similarity: 0.234
  Spatial Pattern: Clustered (Moran's I: 0.342, p=0.045)

=== Vision API Analysis ===
  Objects Detected: graffiti, wall art, spray paint
  Cultural Context: Urban expression, counter-culture symbolism
  Correlation with CLIP: 0.78 (strong positive correlation)
```

## 🛠️ Configuration

### Basic Configuration (`config/default.yaml`)
```yaml
# CLIP Model Settings
model:
  name: "openai/clip-vit-base-patch32"
  batch_size: 16
  cache_embeddings: true

# Spatial Analysis Settings
spatial:
  distance_threshold_km: 1.0
  k_neighbors: 8
  weight_type: "inverse_distance"

# OpenAI Vision API Settings (Optional)
apis:
  openai:
    model: "gpt-4o-mini"        # or gpt-4o
    max_concurrent: 10
    rate_limit_delay: 0.5

# Analysis Settings
vision_analysis:
  enable_qualitative: true      # Rich descriptive analysis
  enable_quantitative: true     # Structured tokens
  custom_template: null         # Path to custom analysis template
```

### Load Configuration
```python
from clip_humanists.core.config import load_config

config = load_config("config/my_project.yaml")
analyzer = EnhancedCLIPAnalyzer(
    model_name=config.model.name,
    batch_size=config.model.batch_size
)
```

## 🎯 Research Examples

### 1. **Urban Semiotics Study**
```python
# Analyze signage patterns across city districts
prompts = ["commercial advertising", "street art", "official signage"]
results = analyze_urban_semiotics("city_photos/", prompts)

# Generate spatial autocorrelation report
spatial_patterns = spatial_analyzer.semantic_autocorrelation(results)
```

### 2. **Cultural Visual Analysis**
```python
# Comprehensive cultural analysis with Vision API
cultural_template = """
Analyze this image for cultural and semiotic elements:
- Visual communication strategies
- Cultural symbols and references
- Compositional techniques
- Emotional and narrative content
"""

results = multimodal_analyzer.analyze_folder(
    "cultural_images/",
    clip_prompts=["traditional", "modern", "symbolic"],
    vision_template=cultural_template
)
```

### 3. **Historical Documentation**
```python
# Temporal analysis of visual culture evolution
temporal_data = organize_images_by_time(image_collection)
evolution_analysis = analyze_cultural_evolution(temporal_data)
```

## 📊 Performance & Costs

### API Usage (Optional)
- **gpt-4o-mini**: ~$0.02 per image (recommended for most research)
- **gpt-4o**: ~$0.15 per image (higher quality analysis)
- **Built-in cost estimation** before analysis

### Optimization Features
- **CLIP Caching**: Intelligent embedding caching reduces recomputation
- **Rate Limiting**: Respects API limits with configurable delays
- **Batch Processing**: Efficient processing of large image collections
- **GPU Acceleration**: Automatic CUDA detection with CPU fallback

## 🔍 Advanced Features

### 1. **Graceful Degradation**
- **Full Version**: With all dependencies → Complete analysis suite
- **Simplified Version**: Basic dependencies → Core functionality
- **Mock Mode**: No API keys → Demonstration with synthetic data

### 2. **Flexible Analysis Templates**
```python
# Custom analysis templates for different research domains
poster_analysis_template = """
Analyze this poster for:
- Character demographics and relationships
- Visual communication strategies
- Cultural symbols and intertextuality
- Compositional techniques
"""

# Apply template to image collection
results = multimodal_analyzer.analyze_with_template(
    image_folder, 
    poster_analysis_template
)
```

### 3. **Statistical Validation**
```python
# Cross-model validation
model_comparison = compare_analysis_methods(clip_results, vision_results)
reliability_report = generate_validation_report(model_comparison)
```

## 🧪 Testing & Validation

### Run Tests
```bash
# Comprehensive test suite
python tests/test_basic_functionality.py

# Expected output: "Test Results: 5/5 tests passed"
```

### Test Coverage
- ✅ Configuration management
- ✅ GPS extraction from EXIF data
- ✅ CLIP model integration
- ✅ Spatial autocorrelation analysis
- ✅ Multimodal content analysis
- ✅ Error handling and fallbacks

## 🚨 Troubleshooting

### Common Issues

**1. Missing OpenAI API Key**
```
Error: OpenAI API key not found
```
**Solution**: Set environment variable: `export OPENAI_API_KEY=your_key_here`

**2. Missing Spatial Libraries**
```
ImportError: No module named 'libpysal'
```
**Solution**: System falls back to simplified analysis. For full features: `pip install libpysal esda`

**3. GPU Memory Issues**
```
RuntimeError: CUDA out of memory
```
**Solution**: Reduce batch size in config: `batch_size: 8`

**4. No GPS Data Found**
```
Warning: No images with valid GPS coordinates
```
**Solution**: Ensure images contain EXIF GPS data, or use mock data for testing

## 📚 Documentation

### Examples
- `examples/demo_with_sample_data.py` - Basic CLIP and spatial analysis
- `examples/multimodal_analysis_demo.py` - Complete multimodal analysis
- `examples/basic_autocorrelation_demo.py` - Spatial analysis focused

### Configuration
- `config/default.yaml` - Default settings
- `config/models.yaml` - Model presets and templates

## 🤝 Migration Guide

### For Existing CLIP for Humanists Users
✅ **No Breaking Changes**: All existing functionality remains unchanged
✅ **Additive Features**: New multimodal capabilities are optional extensions
✅ **Backward Compatibility**: Existing configurations continue to work

### For New Users
✅ **Multiple Entry Points**: Start with basic CLIP analysis or full multimodal pipeline
✅ **Comprehensive Documentation**: Step-by-step guides for different research needs
✅ **Example Workflows**: Pre-configured analysis pipelines

## 🎯 Roadmap

### Current Capabilities (v2.0)
- ✅ Advanced CLIP analysis with spatial autocorrelation
- ✅ OpenAI Vision API integration
- ✅ Multimodal content analysis
- ✅ Cross-analysis correlation
- ✅ Comprehensive configuration management

### Planned Features
- [ ] CLI interface with subcommands
- [ ] Interactive web dashboard
- [ ] Temporal trend analysis
- [ ] Advanced visualization suite
- [ ] Integration with additional vision models
- [ ] Export capabilities (GeoJSON, comprehensive reports)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Original CLIP for Humanists project
- OpenAI CLIP model and Vision API
- PySAL spatial analysis library
- Transformers library by Hugging Face
- Poster analysis research methodology

## 📞 Support

For questions, issues, or contributions:
1. **GitHub Issues**: Report bugs and request features
2. **Discussions**: Ask questions and share use cases
3. **Documentation**: Check comprehensive examples in `examples/`

---

**CLIP for Humanists v2.0** - A comprehensive multimodal analysis platform that bridges computational methods with cultural interpretation, enabling advanced digital humanities research at scale.