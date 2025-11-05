# Phase 3: Visualization Layer - Implementation Plan

**Start Date**: November 5, 2025
**Estimated Duration**: 4-6 weeks
**Status**: In Progress

---

## Overview

Phase 3 will migrate all visualization capabilities from the Colab notebook (`src/visualization.py`) into the Django application, making CLIP analysis results accessible, interactive, and exportable.

---

## Existing Visualization Functions (from src/visualization.py)

### 1. **plot_similarity_heatmap**
- **Purpose**: Create heatmap of image-text similarities
- **Input**: Dict of image paths → text prompts → scores
- **Output**: Matplotlib figure
- **Priority**: HIGH ⭐⭐⭐

### 2. **create_map_with_images**
- **Purpose**: Interactive Folium map with image markers at GPS coordinates
- **Input**: List of image data with GPS coordinates
- **Output**: Folium map HTML
- **Priority**: HIGH ⭐⭐⭐

### 3. **plot_similarity_by_location**
- **Purpose**: Scatter plot of images by GPS location colored by similarity
- **Input**: Image data with GPS and similarity scores
- **Output**: Matplotlib figure
- **Priority**: MEDIUM ⭐⭐

### 4. **display_image_grid**
- **Purpose**: Grid of images sorted by similarity score
- **Input**: Image paths and scores
- **Output**: PIL Image (composite grid)
- **Priority**: HIGH ⭐⭐⭐

### 5. **create_image_with_similarity_bars**
- **Purpose**: Single image with bar chart of concept scores
- **Input**: Image path and similarity dict
- **Output**: Matplotlib figure
- **Priority**: MEDIUM ⭐⭐

### 6. **create_all_image_similarity_bars**
- **Purpose**: Multiple images each with their bar charts
- **Input**: All images and similarities
- **Output**: List of Matplotlib figures
- **Priority**: LOW ⭐

### 7. **create_similarity_correlation_matrix**
- **Purpose**: Correlation heatmap between concepts
- **Input**: Similarities data
- **Output**: Matplotlib figure
- **Priority**: HIGH ⭐⭐⭐

### 8. **create_similarity_violin_plot**
- **Purpose**: Distribution of scores per concept
- **Input**: Similarities data
- **Output**: Matplotlib figure
- **Priority**: MEDIUM ⭐⭐

### 9-12. **Location-based functions**
- normalize_coordinates, cluster_locations, create_location_correlation_plot, calculate_location_similarity_correlation
- **Purpose**: Advanced GPS-based analysis
- **Priority**: LOW ⭐ (Future enhancement)

---

## Django Implementation Strategy

### Architecture

```
apps/visualizations/
├── models.py               # Visualization metadata
├── generators/             # NEW: Visualization generation modules
│   ├── __init__.py
│   ├── base.py            # Base generator class
│   ├── heatmaps.py        # Similarity heatmaps
│   ├── distributions.py   # Violin plots, histograms
│   ├── correlations.py    # Correlation matrices
│   ├── grids.py           # Image grids
│   ├── maps.py            # Interactive maps
│   └── charts.py          # Bar charts, scatter plots
├── tasks.py                # Celery tasks for async generation
├── views.py                # Visualization display views
├── serializers.py          # API serializers
└── utils.py                # Helper functions

templates/visualizations/
├── visualization_list.html
├── visualization_detail.html
├── visualization_gallery.html
└── partials/
    ├── heatmap.html
    ├── map.html
    └── chart.html
```

---

## Implementation Phases

### Phase 3.1: Foundation (Week 1) ✅ Models & Base Classes

**Tasks:**
1. ✅ Update Visualization model (already exists)
2. Create base generator class
3. Set up file storage for generated visualizations
4. Create Celery task infrastructure
5. Add visualization types enum

**Deliverables:**
- Base generator abstract class
- File management utilities
- Async task framework

---

### Phase 3.2: Core Visualizations (Week 2-3) 🎯 Top Priority

**Priority 1: Similarity Heatmap** ⭐⭐⭐
- Migrate `plot_similarity_heatmap` function
- Generate matplotlib figure
- Save as PNG/SVG
- Display in web interface
- Make interactive (zoom, pan)

**Priority 2: Image Grid** ⭐⭐⭐
- Migrate `display_image_grid` function
- Create sortable/filterable grid
- Add pagination for large datasets
- Show similarity scores on hover
- Click to view full image

**Priority 3: Correlation Matrix** ⭐⭐⭐
- Migrate `create_similarity_correlation_matrix`
- Show concept relationships
- Interactive hover for values
- Exportable as CSV

**Deliverables:**
- 3 working visualization generators
- Web UI for viewing each type
- Export functionality (PNG, SVG, PDF)

---

### Phase 3.3: Distribution Visualizations (Week 3-4)

**Tasks:**
1. Implement violin plot generator (`create_similarity_violin_plot`)
2. Add histogram generator
3. Add box plot generator
4. Create comparison views (side-by-side)

**Deliverables:**
- Score distribution visualizations
- Statistical summaries
- Multi-analysis comparison

---

### Phase 3.4: Interactive Maps (Week 4-5)

**Tasks:**
1. Migrate `create_map_with_images` (Folium)
2. Implement `plot_similarity_by_location`
3. Add clustering visualization
4. Create location-based filtering

**Deliverables:**
- Interactive map with image markers
- GPS-based similarity analysis
- Location clustering view

---

### Phase 3.5: Export & Gallery (Week 5-6)

**Tasks:**
1. Implement CSV export
2. Implement JSON export
3. Implement ZIP download (all visualizations)
4. Create visualization gallery/browser
5. Add batch generation

**Deliverables:**
- Complete export system
- Visualization gallery interface
- Batch processing for multiple analyses

---

## Technical Requirements

### Dependencies to Add

```python
# requirements-django.txt additions:
matplotlib>=3.8.0
seaborn>=0.13.0          # Better statistical plots
plotly>=5.18.0           # Interactive charts (optional)
folium>=0.15.0           # Interactive maps
Pillow>=10.0.0           # Already installed
scipy>=1.11.0            # Statistical functions
scikit-learn>=1.3.0      # Clustering
```

### Storage Strategy

```python
# In settings.py
VISUALIZATION_ROOT = MEDIA_ROOT / 'visualizations'
VISUALIZATION_URL = MEDIA_URL + 'visualizations/'

# File structure:
# media/visualizations/
#   ├── analysis_123/
#   │   ├── heatmap_456.png
#   │   ├── correlation_789.png
#   │   ├── violin_101.png
#   │   └── map_202.html
```

### Model Enhancements

```python
class Visualization(models.Model):
    VIZ_TYPES = [
        ('heatmap', 'Similarity Heatmap'),
        ('correlation', 'Correlation Matrix'),
        ('violin', 'Violin Plot'),
        ('histogram', 'Histogram'),
        ('grid', 'Image Grid'),
        ('map', 'Interactive Map'),
        ('scatter', 'Scatter Plot'),
        ('bars', 'Bar Chart'),
    ]

    viz_type = models.CharField(max_length=20, choices=VIZ_TYPES)
    file = models.FileField(upload_to='visualizations/')
    thumbnail = models.ImageField(upload_to='visualizations/thumbnails/', null=True)
    format = models.CharField(max_length=10)  # png, svg, pdf, html
    metadata = models.JSONField(default=dict)  # Chart configuration
```

---

## API Endpoints

### Visualization Endpoints

```
GET    /api/v1/visualizations/                    # List all visualizations
GET    /api/v1/visualizations/{id}/                # Get visualization details
POST   /api/v1/visualizations/generate/            # Generate new visualization
DELETE /api/v1/visualizations/{id}/                # Delete visualization

# Analysis-specific
GET    /api/v1/analyses/{id}/visualizations/       # Get all visualizations for analysis
POST   /api/v1/analyses/{id}/visualizations/generate/  # Generate for analysis

# Bulk operations
POST   /api/v1/analyses/{id}/visualizations/generate-all/  # Generate all types
GET    /api/v1/analyses/{id}/export/zip/           # Download all as ZIP
```

---

## UI/UX Design

### Visualization Gallery

```
┌─────────────────────────────────────────────────────┐
│  Analysis: Urban Imagery Analysis                   │
│  ┌─────────┬─────────┬─────────┬─────────┐        │
│  │ [🔥]    │ [📊]    │ [🎻]    │ [🗺️]    │        │
│  │ Heatmap │ Corr.   │ Violin  │ Map     │        │
│  │ ▼       │         │         │         │        │
│  └─────────┴─────────┴─────────┴─────────┘        │
│                                                     │
│  ┌───────────────────────────────────────────┐    │
│  │                                            │    │
│  │         [HEATMAP VISUALIZATION]           │    │
│  │                                            │    │
│  │  architecture  ████████████  0.87         │    │
│  │  nature        ██████        0.65         │    │
│  │  people        ███████       0.72         │    │
│  │                                            │    │
│  └───────────────────────────────────────────┘    │
│                                                     │
│  [📥 Download PNG]  [📄 Export Data]  [🔄 Regenerate]│
└─────────────────────────────────────────────────────┘
```

### Interactive Controls

- **Filter by score**: Slider to adjust threshold
- **Select concepts**: Checkbox list
- **Sort options**: By score, name, date
- **View modes**: Grid, list, gallery
- **Export options**: PNG, SVG, PDF, CSV, JSON

---

## Success Metrics

### Performance Targets
- Heatmap generation: < 3 seconds for 100 images
- Map generation: < 5 seconds for 100 locations
- Grid generation: < 2 seconds for 50 images
- Page load time: < 2 seconds

### Quality Targets
- All visualizations render correctly
- Interactive elements work smoothly
- Export formats are valid
- Mobile responsive (at least view mode)

---

## Testing Strategy

### Unit Tests
- Test each generator function
- Test data transformation
- Test file creation
- Test error handling

### Integration Tests
- Test Celery task execution
- Test file storage and retrieval
- Test API endpoints
- Test template rendering

### Visual Regression Tests (Future)
- Screenshot comparison
- Chart accuracy validation

---

## Migration Checklist

### Week 1: Foundation
- [ ] Create generators/ module structure
- [ ] Implement BaseGenerator class
- [ ] Set up file storage
- [ ] Add Celery tasks
- [ ] Update Visualization model

### Week 2: Core Visualizations
- [ ] Implement HeatmapGenerator
- [ ] Implement GridGenerator
- [ ] Implement CorrelationGenerator
- [ ] Create display templates
- [ ] Add export functionality

### Week 3: Distributions
- [ ] Implement ViolinPlotGenerator
- [ ] Implement HistogramGenerator
- [ ] Create comparison views
- [ ] Add statistical summaries

### Week 4: Maps
- [ ] Implement MapGenerator (Folium)
- [ ] Implement LocationScatterGenerator
- [ ] Add clustering visualization
- [ ] Create location filter UI

### Week 5: Export & Polish
- [ ] Implement CSV exporter
- [ ] Implement JSON exporter
- [ ] Implement ZIP bundler
- [ ] Create gallery interface
- [ ] Add batch generation

### Week 6: Testing & Documentation
- [ ] Write comprehensive tests
- [ ] Performance optimization
- [ ] User documentation
- [ ] API documentation
- [ ] Code review and cleanup

---

## Risk Assessment

### Technical Risks

**Risk**: Matplotlib memory issues with large datasets
**Mitigation**: Implement pagination, lazy loading, image size limits

**Risk**: Folium maps slow with 1000+ markers
**Mitigation**: Implement clustering, marker grouping, lazy loading

**Risk**: File storage fills up quickly
**Mitigation**: Implement cleanup tasks, size limits, compression

### UX Risks

**Risk**: Users don't understand visualizations
**Mitigation**: Add explanatory text, tooltips, help documentation

**Risk**: Slow generation frustrates users
**Mitigation**: Clear progress indicators, async generation, caching

---

## Future Enhancements (Phase 6+)

1. **Interactive Charts with Plotly**
   - Zoom, pan, filter in browser
   - No regeneration needed

2. **Real-time Streaming**
   - WebSocket updates as visualization generates
   - Progressive rendering

3. **Customization Options**
   - Color schemes
   - Chart types
   - Size and resolution

4. **Sharing & Embedding**
   - Public visualization URLs
   - Embed codes for websites
   - Social media previews

5. **Advanced Analytics**
   - Time-series analysis
   - Trend detection
   - Anomaly highlighting

---

## Timeline Summary

```
Week 1:  Foundation & Setup
Week 2:  Heatmap, Grid, Correlation
Week 3:  Distributions (Violin, Histogram)
Week 4:  Interactive Maps
Week 5:  Export & Gallery
Week 6:  Testing & Polish

Total: 6 weeks to complete Phase 3
```

---

## Success Criteria

Phase 3 is considered complete when:

✅ All 12 visualization types are implemented
✅ Users can generate visualizations from any analysis
✅ Visualizations are viewable in web interface
✅ Export functionality works (PNG, CSV, JSON, ZIP)
✅ Interactive maps are functional
✅ Gallery/browser interface is complete
✅ Tests achieve 80%+ coverage
✅ Documentation is published
✅ Performance targets are met

---

**Ready to begin implementation!** 🚀
