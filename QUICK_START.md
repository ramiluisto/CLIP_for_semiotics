# CLIP for Humanists - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```bash
# Basic installation (works without heavy spatial libraries)
pip install -r requirements.txt

# Optional: Full spatial analysis capabilities
pip install libpysal esda pysal geopandas
```

### 2. Test the Installation

```bash
# Run the basic functionality test
python tests/test_basic_functionality.py

# Expected output: "🎉 All basic functionality tests passed!"
```

### 3. Try the Demo

```bash
# Run the complete demonstration
python examples/demo_with_sample_data.py
```

This will:
- Process the sample images in `img/` folder
- Extract GPS data from EXIF metadata
- Perform semantic similarity analysis
- Calculate spatial autocorrelation statistics
- Display comprehensive results

### 4. Basic Usage

```python
from clip_humanists import EnhancedCLIPAnalyzer, GPSExtractor, SpatialAutocorrelation

# Initialize components
clip_analyzer = EnhancedCLIPAnalyzer()
gps_extractor = GPSExtractor()
spatial_analyzer = SpatialAutocorrelation()

# Process your images
prompts = ["street art", "signage", "architecture"]
gps_results = gps_extractor.extract_from_folder("path/to/images")
clip_results = clip_analyzer.analyze_folder("path/to/images", prompts)

# Combine results (simplified example)
combined_data = []
for clip_result in clip_results:
    gps_result = next((g for g in gps_results if g.filepath == clip_result.filepath), None)
    if gps_result and gps_result.gps_coordinates:
        clip_result.gps_coordinates = gps_result.gps_coordinates
        combined_data.append(clip_result)

# Analyze spatial patterns
moran_results = spatial_analyzer.morans_i(combined_data, "street art")
print(f"Moran's I: {moran_results.statistic:.3f} (p={moran_results.p_value:.3f})")
```

### 5. Configuration

Edit `config/default.yaml` to customize:

```yaml
model:
  name: "openai/clip-vit-base-patch32"  # Choose your model
  batch_size: 16                        # Adjust for your hardware

spatial:
  distance_threshold_km: 1.0            # Spatial analysis range
  weight_type: "inverse_distance"       # Spatial weighting method
```

## 📊 Understanding Results

### Spatial Autocorrelation
- **Moran's I > 0**: Similar values cluster together (positive autocorrelation)
- **Moran's I < 0**: Dissimilar values cluster together (negative autocorrelation)  
- **p-value < 0.05**: Statistically significant pattern
- **p-value ≥ 0.05**: Random spatial distribution

### Example Output
```
Prompt: 'street art'
  Moran's I: 0.342
  P-value: 0.045
  Interpretation: Significant positive spatial autocorrelation (clustered)
```

This means street art tends to cluster in specific areas rather than being randomly distributed.

## 🔧 Troubleshooting

### No GPS Data Found
**Problem**: "No images with valid GPS coordinates"
**Solution**: Ensure your images contain EXIF GPS data, or use the demo which includes mock data

### Missing Dependencies
**Problem**: "No module named 'libpysal'"
**Solution**: The system automatically uses simplified analysis. For full features: `pip install libpysal esda`

### GPU Memory Issues
**Problem**: "CUDA out of memory"
**Solution**: Reduce batch size in config: `batch_size: 8`

## 📚 Next Steps

1. **Read the full documentation**: `README.md`
2. **Explore examples**: Check `examples/` folder
3. **Customize configuration**: Edit `config/default.yaml`
4. **Try with your own images**: Replace images in `img/` folder or specify your own path

## 🎯 Research Applications

- **Urban Semiotics**: Analyze signage patterns across city districts
- **Cultural Geography**: Map visual culture across regions
- **Digital Ethnography**: Systematic analysis of visual social media data
- **Art History**: Spatial distribution of artistic themes

Ready to explore visual patterns in your research? Start with the demo and adapt the code for your specific needs!