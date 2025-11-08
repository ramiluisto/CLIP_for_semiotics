# CLIP for Humanists

A tool to aid the discovery process of visual semiotical analysis and geosemiotical analysis using CLIP (Contrastive Language-Image Pre-training).

## Overview

CLIP for Humanists helps researchers analyze images by:

1. Extracting GPS data from images to visualize geographical locations
2. Comparing images with keywords/phrases using CLIP
3. Visualizing trends and correlations between images and text
4. Identifying patterns that might be useful for semiotical analysis

This tool is designed to be accessible to non-technical users through a Google Colab notebook.

## Features

- Extract and visualize GPS data from images
- Compare images with custom keywords using CLIP
- Create heatmaps of image-text similarities
- Display images on interactive maps
- Analyze similarities by location
- Find top-matching images for specific concepts

## Getting Started

The easiest way to use CLIP for Humanists is through our Google Colab notebook:

[Open in Google Colab](https://colab.research.google.com/github/yourusername/CLIP_for_humanists/blob/main/CLIP_for_Humanists.ipynb)

### Local Installation

If you prefer to run the tool locally:

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/CLIP_for_humanists.git
   cd CLIP_for_humanists
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Run the example script:

   ```
   python examples/basic_analysis.py
   ```

## Project Structure

```
CLIP_for_humanists/
├── CLIP_for_Humanists.ipynb  # Main Google Colab notebook
├── README.md                 # This file
├── requirements.txt          # Dependencies
├── src/                      # Source code
│   ├── __init__.py
│   ├── clip_utils.py         # CLIP functionality
│   ├── gps_utils.py          # GPS extraction
│   ├── main.py               # Main functionality
│   └── visualization.py      # Visualization tools
├── img/                      # Example images
└── tests/                    # Unit tests
```

## Usage Example

```python
from src.main import ClipForHumanists

# Initialize the system
cfh = ClipForHumanists()

# Define text prompts for comparison
text_prompts = ["scary", "friendly", "warning", "information"]

# Process images
results = cfh.process_images("path/to/images", text_prompts)

# Create visualizations
heatmap = cfh.create_similarity_heatmap()
map_viz = cfh.create_map()
grid = cfh.create_image_grid(text_prompt="warning")

# Get top images for a concept
top_scary = cfh.get_top_images_for_prompt("scary", n=5)
```

## For Non-Technical Users

This tool is designed to be accessible to users without programming experience. The Google Colab notebook provides step-by-step instructions for:

1. Uploading your images
2. Specifying keywords for analysis
3. Generating visualizations
4. Interpreting the results

No coding knowledge is required to use the notebook.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for the CLIP model
- The semiotics research community for inspiration and feedback
