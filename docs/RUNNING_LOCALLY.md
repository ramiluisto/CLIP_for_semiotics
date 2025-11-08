# Running CLIP for Humanists Locally

**Note:** These instructions are for users who want to run the CLIP for Humanists tool locally on their own machine. If you're using the provided notebook in Google Colab or another hosted environment, you don't need to follow these instructions.

## Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.8 or newer
- pip (Python package manager)
- Git (optional, for cloning the repository)

## Installation Steps

### 1. Clone or Download the Repository

You can either download the ZIP file from GitHub or clone the repository:

```bash
git clone https://github.com/yourusername/CLIP_for_humanists.git
cd CLIP_for_humanists
```

### 2. Set Up a Virtual Environment (Recommended)

It's a good practice to create a virtual environment to keep the dependencies isolated:

```bash
# Using venv (built into Python)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

This will install all necessary packages including:

- PyTorch
- transformers
- Pillow
- matplotlib
- pandas
- folium
- scikit-learn
- scipy

### 4. Verify Installation

Run a simple example to verify that everything is working:

```bash
python examples/basic_analysis.py
```

This will process the sample images in the `img` folder and generate outputs in the `output` folder.

## Usage

### Using the Library in Your Own Scripts

You can use the CLIP for Humanists library in your own Python scripts:

```python
from src.main import ClipForHumanists

# Initialize
cfh = ClipForHumanists()

# Process images with text prompts
text_prompts = ["concept1", "concept2", "concept3"]
results = cfh.process_images("path/to/your/images", text_prompts)

# Generate visualizations
heatmap = cfh.create_similarity_heatmap()
heatmap.savefig("similarity_heatmap.png")

# If your images have GPS data
cfh.normalize_coordinates()
location_plot = cfh.create_location_correlation_plot(text_prompt="concept1")
location_plot.savefig("location_correlation.png")

# Create individual image analyses
cfh.create_all_image_similarity_bars()

# Save results to JSON
cfh.save_results("my_results.json")
```

### Basic Example Script

The repository includes an example script (`examples/basic_analysis.py`) that demonstrates all the functionality. You can modify this script for your own analysis.

## Troubleshooting

### Common Issues

1. **CUDA/GPU Issues**: If you encounter CUDA-related errors, the code will automatically fall back to CPU. You can explicitly use CPU by adding `device="cpu"` when initializing:

   ```python
   cfh = ClipForHumanists(device="cpu")
   ```

2. **Memory Issues**: Processing large images or many images at once can cause memory issues. Try processing smaller batches or resizing images if you encounter memory problems.

3. **Missing Dependencies**: If you encounter an ImportError, make sure all dependencies are installed:

   ```bash
   pip install -r requirements.txt
   ```

4. **CLIP Model Download**: The first time you run the tool, it will download the CLIP model (about 600MB). Make sure you have a stable internet connection.

### Getting Help

If you encounter any issues not covered here, please check the GitHub repository issues or create a new issue with:

1. The command you were trying to run
2. The complete error message
3. Your operating system and Python version
4. Any other relevant information

## Uninstallation

To uninstall, simply remove the project directory and (if you used one) deactivate and delete the virtual environment:

```bash
# Deactivate virtual environment
deactivate

# Remove project directory
cd ..
rm -rf CLIP_for_humanists  # Linux/macOS
# or
rmdir /s /q CLIP_for_humanists  # Windows
```
