"""
Basic example of using CLIP for Humanists.
"""

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from src.main import ClipForHumanists

# Define the path to the example images
img_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "img")

# Define text prompts for comparison
text_prompts = ["scary", "friendly", "warning", "information", "official"]

# Create output directory structure
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
img_output_dir = os.path.join(output_dir, "images")
data_output_dir = os.path.join(output_dir, "data")
report_output_dir = os.path.join(output_dir, "reports")
result_images_dir = os.path.join(output_dir, "result_images")

# Create directories if they don't exist
for directory in [
    output_dir,
    img_output_dir,
    data_output_dir,
    report_output_dir,
    result_images_dir,
]:
    os.makedirs(directory, exist_ok=True)

# Initialize the system
cfh = ClipForHumanists()

# Process images
print(f"Processing images in {img_folder}...")
results = cfh.process_images(img_folder, text_prompts)
print(f"Processed {len(results)} images")

# Create a heatmap of image-text similarities
print("Creating similarity heatmap...")
heatmap_fig = cfh.create_similarity_heatmap(title="Image-Text Similarity Heatmap")
# Save the figure to the images output directory
heatmap_path = os.path.join(img_output_dir, "similarity_heatmap.png")
heatmap_fig.savefig(heatmap_path)
plt.close(heatmap_fig)
print(f"Saved similarity heatmap to {heatmap_path}")

# Create violin plot to show the distributions of similarity scores
print("Creating similarity score distribution violin plot...")
violin_fig = cfh.create_similarity_violin_plot(
    title="Distribution of Similarity Scores Across All Images"
)
violin_path = os.path.join(img_output_dir, "similarity_distribution.png")
violin_fig.savefig(violin_path)
plt.close(violin_fig)
print(f"Saved similarity distribution to {violin_path}")

# Check if any images have GPS coordinates
has_gps = any(item.get("gps_coordinates") is not None for item in cfh.image_data)
if has_gps:
    # Create a map with images at their GPS coordinates
    print("Creating map with images...")
    map_obj = cfh.create_map(zoom_start=13)
    map_path = os.path.join(report_output_dir, "image_map.html")
    map_obj.save(map_path)
    print(f"Saved map to {map_path}")

    # Normalize coordinates for analysis
    print("Normalizing coordinates...")
    cfh.normalize_coordinates()

    # Cluster locations
    print("Clustering locations...")
    cfh.cluster_locations(n_clusters=3)

    # Create correlation plots for each text prompt
    print("Creating location-similarity correlation plots...")
    for prompt in text_prompts:
        fig = cfh.create_location_correlation_plot(
            text_prompt=prompt,
            title=f"Correlation between Location and Similarity for '{prompt}'",
        )
        corr_path = os.path.join(img_output_dir, f"location_correlation_{prompt}.png")
        fig.savefig(corr_path)
        plt.close(fig)
        print(f"Saved location correlation plot for '{prompt}' to {corr_path}")

    # Calculate correlations between location and similarity
    print("Calculating location-similarity correlations...")
    corr_df = cfh.calculate_location_similarity_correlation()
    print("\nLocation-Similarity Correlations:")
    print(corr_df.to_string(index=False))

    # Save correlation data to CSV
    corr_csv_path = os.path.join(data_output_dir, "location_correlations.csv")
    corr_df.to_csv(corr_csv_path, index=False)
    print(f"Saved location correlations to {corr_csv_path}")

# Create individual images with similarity bars
print("Creating images with similarity bars...")
cfh.create_all_image_similarity_bars(output_dir=result_images_dir)
print(f"Saved images with similarity bars to {result_images_dir}")

# Create a correlation matrix of concepts
print("Creating concept correlation matrix...")
corr_fig = cfh.create_similarity_correlation_matrix()
concept_corr_path = os.path.join(img_output_dir, "concept_correlations.png")
corr_fig.savefig(concept_corr_path)
plt.close(corr_fig)
print(f"Saved concept correlations to {concept_corr_path}")

# Save results to JSON
print("Saving results to JSON...")
results_path = os.path.join(data_output_dir, "clip_humanists_results.json")
cfh.save_results(results_path)
print(f"Saved results to {results_path}")
