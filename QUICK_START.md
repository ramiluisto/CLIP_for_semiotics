# CLIP for Humanists - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```bash
# Basic installation (core CLIP + spatial analysis)
pip install -r requirements.txt

# Optional: Full spatial analysis capabilities
pip install libpysal esda pysal geopandas

# Optional: OpenAI Vision API for multimodal analysis
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

## 📊 What Each Demo Shows

### Basic Demo (`demo_with_sample_data.py`)
- GPS data extraction from EXIF
- CLIP similarity analysis
- Spatial autocorrelation (Moran's I)
- Statistical reporting

### Multimodal Demo (`multimodal_analysis_demo.py`)
- All basic features PLUS:
- OpenAI Vision API content analysis
- Cross-analysis correlation
- Cultural and semiotic analysis
- Dual-format outputs (qualitative + quantitative)

## 🔬 Basic Usage Patterns

### 1. **CLIP-only Analysis**
```python
from clip_humanists import EnhancedCLIPAnalyzer, GPSExtractor, SpatialAutocorrelation

# Initialize components
clip_analyzer = EnhancedCLIPAnalyzer()
gps_extractor = GPSExtractor()
spatial_analyzer = SpatialAutocorrelation()

# Process images
prompts = ["street art", "signage", "architecture"]
gps_results = gps_extractor.extract_from_folder("path/to/images")
clip_results = clip_analyzer.analyze_folder("path/to/images", prompts)

# Combine and analyze spatial patterns
combined_data = []
for clip_result in clip_results:
    gps_result = next((g for g in gps_results if g.filepath == clip_result.filepath), None)
    if gps_result and gps_result.gps_coordinates:
        clip_result.gps_coordinates = gps_result.gps_coordinates
        combined_data.append(clip_result)

# Spatial autocorrelation analysis
moran_results = spatial_analyzer.morans_i(combined_data, "street art")
print(f"Moran's I: {moran_results.statistic:.3f} (p={moran_results.p_value:.3f})")
```

### 2. **Multimodal Analysis** (requires OpenAI API key)
```python
from clip_humanists import MultimodalContentAnalyzer

# Initialize multimodal analyzer
analyzer = MultimodalContentAnalyzer(
    enable_clip=True,      # Quantitative similarity analysis
    enable_vision=True,    # Qualitative content analysis
    enable_gps=True        # Spatial data extraction
)

# Define analysis prompts
clip_prompts = ["street art", "signage", "architecture"]
vision_template = """
Analyze this image for:
- Visual communication strategies
- Cultural symbols and references
- Compositional techniques
- Emotional and narrative content
"""

# Run comprehensive analysis
results = analyzer.analyze_folder(
    "path/to/images",
    clip_prompts=clip_prompts,
    vision_template=vision_template
)

# Get cross-analysis correlations
correlations = analyzer.get_cross_analysis_correlations(results)
```

### 3. **Configuration Customization**
```python
from clip_humanists.core.config import load_config

# Load custom configuration
config = load_config("config/my_project.yaml")

# Use with specific settings
analyzer = EnhancedCLIPAnalyzer(
    model_name=config.model.name,
    batch_size=config.model.batch_size
)
```

## 🛠️ Basic Configuration

Edit `config/default.yaml` to customize:

```yaml
# CLIP Model Settings
model:
  name: "openai/clip-vit-base-patch32"  # Choose your model
  batch_size: 16                        # Adjust for your hardware
  cache_embeddings: true                # Enable caching for speed

# Spatial Analysis Settings
spatial:
  distance_threshold_km: 1.0            # Spatial analysis range
  k_neighbors: 8                        # Number of neighbors
  weight_type: "inverse_distance"       # Spatial weighting method

# OpenAI Vision API Settings (Optional)
apis:
  openai:
    model: "gpt-4o-mini"                # Cost-effective option
    max_concurrent: 10                  # Rate limiting
    rate_limit_delay: 0.5               # Delay between requests

# Analysis Settings
vision_analysis:
  enable_qualitative: true             # Rich descriptive analysis
  enable_quantitative: true            # Structured tokens
```

## 📊 Understanding Results

### CLIP Analysis Results
```python
# Each image gets similarity scores for all prompts
{
    "filepath": "image.jpg",
    "similarities": {
        "street art": 0.234,
        "signage": 0.156,
        "architecture": 0.089
    },
    "gps_coordinates": (lat, lon)
}
```

### Spatial Autocorrelation
- **Moran's I > 0**: Similar values cluster together (positive autocorrelation)
- **Moran's I < 0**: Dissimilar values cluster together (negative autocorrelation)
- **Moran's I ≈ 0**: Random spatial distribution
- **p-value < 0.05**: Statistically significant pattern

### Vision API Analysis (when enabled)
```python
# Rich content analysis
{
    "qualitative_analysis": "This image shows urban street art...",
    "quantitative_format": {
        "objects": ["graffiti", "wall", "spray_paint"],
        "colors": ["red", "blue", "black"],
        "cultural_context": ["urban_expression", "counter_culture"]
    },
    "cross_correlations": {
        "clip_matches": ["street art correlation: 0.78"]
    }
}
```

## 🔧 Troubleshooting

### Common Issues

**1. No OpenAI API Key (for multimodal features)**
```
Error: OpenAI API key not found
```
**Solution**: Set environment variable: `export OPENAI_API_KEY=your_key_here`
Or run basic demo without multimodal features

**2. Missing Dependencies**
```
ImportError: No module named 'libpysal'
```
**Solution**: The system automatically uses simplified analysis. For full features: 
```bash
pip install libpysal esda pysal geopandas
```

**3. GPU Memory Issues**
```
RuntimeError: CUDA out of memory
```
**Solution**: Reduce batch size in config: `batch_size: 8`

**4. No GPS Data Found**
```
Warning: No images with valid GPS coordinates
```
**Solution**: Ensure images contain EXIF GPS data, or use demo images which include GPS data

## 📚 Next Steps

### 1. **Choose Your Analysis Type**
- **Basic Research**: Start with CLIP analysis and spatial autocorrelation
- **Advanced Research**: Use multimodal analysis with Vision API
- **Cultural Studies**: Focus on qualitative analysis templates

### 2. **Customize for Your Research**
- **Urban Studies**: Use prompts like "signage", "street art", "commercial"
- **Cultural Analysis**: Use custom vision templates for cultural context
- **Historical Research**: Include temporal analysis with image timestamps

### 3. **Scale Your Analysis**
- **Small Collections**: Use basic batch processing
- **Large Collections**: Enable caching and optimize batch sizes
- **Archival Research**: Consider cost estimation for Vision API usage

### 4. **Advanced Features**
- **Custom Templates**: Create analysis templates for your research domain
- **Statistical Validation**: Use cross-model comparison for reliability
- **Temporal Analysis**: Organize by time periods for longitudinal studies

## 🎯 Research Application Examples

### Urban Semiotics
```python
# Analyze signage patterns across city districts
urban_prompts = ["commercial advertising", "street art", "official signage"]
results = analyze_urban_semiotics("city_photos/", urban_prompts)
```

### Cultural Geography
```python
# Map visual culture across regions
cultural_prompts = ["traditional symbols", "modern design", "cultural expressions"]
cultural_analysis = analyze_cultural_geography("regional_images/", cultural_prompts)
```

### Digital Ethnography
```python
# Systematic analysis of visual culture
ethnographic_template = """
Analyze this image for cultural and social elements:
- Social interactions and relationships
- Cultural symbols and meanings
- Environmental context
- Temporal markers and trends
"""
results = multimodal_analyzer.analyze_with_template(images, ethnographic_template)
```

## 📖 Additional Resources

- **Full Documentation**: `README.md` - Comprehensive guide
- **Example Scripts**: `examples/` - Ready-to-use analysis scripts
- **Configuration**: `config/` - Settings and presets
- **Test Suite**: `tests/` - Verify installation and functionality

Ready to analyze visual patterns in your research? Start with the basic demo and expand to multimodal analysis as your needs grow!