"""
Main module for CLIP for Humanists.
"""

from typing import Dict, List, Optional, Tuple, Union
import os
import pandas as pd
import json
import matplotlib.pyplot as plt

from src.gps_utils import extract_gps_from_folder, get_closest_location_tag
from src.clip_utils import ClipAnalyzer
from src.visualization import (
    plot_similarity_heatmap,
    create_map_with_images,
    plot_similarity_by_location,
    display_image_grid,
    create_image_with_similarity_bars,
    create_all_image_similarity_bars,
    create_similarity_correlation_matrix,
    normalize_coordinates,
    cluster_locations,
    create_location_correlation_plot,
    calculate_location_similarity_correlation,
    create_similarity_violin_plot,
)


class ClipForHumanists:
    """
    Main class for CLIP for Humanists.
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize the CLIP for Humanists system.

        Args:
            model_name: Name of the CLIP model to use
        """
        self.clip_analyzer = ClipAnalyzer(model_name)
        self.image_data = []
        self.location_dict = {}

    def set_location_dict(self, location_dict: Dict[str, Tuple[float, float]]):
        """
        Set the dictionary of locations.

        Args:
            location_dict: Dictionary mapping location names to (lat, lon) coordinates
        """
        self.location_dict = location_dict

    def process_images(
        self, folder_path: str, text_prompts: List[str]
    ) -> List[
        Dict[str, Union[str, Tuple[float, float], Dict[str, float], Optional[str]]]
    ]:
        """
        Process all images in a folder.

        Args:
            folder_path: Path to the folder containing images
            text_prompts: List of text prompts to compare with the images

        Returns:
            List of dictionaries with image data
        """
        # Extract GPS data
        print("Extracting GPS data...")
        gps_data = extract_gps_from_folder(folder_path, self.location_dict)

        # Analyze images with CLIP
        print("Analyzing images with CLIP...")
        clip_results = self.clip_analyzer.analyze_folder(folder_path, text_prompts)

        # Combine results
        self.image_data = []
        for gps_item in gps_data:
            filepath = gps_item["filepath"]

            # Find corresponding CLIP result
            clip_item = next(
                (item for item in clip_results if item["filepath"] == filepath), None
            )

            if clip_item:
                combined_item = {
                    "filepath": filepath,
                    "gps_coordinates": gps_item["gps_coordinates"],
                    "similarities": clip_item["similarities"],
                }

                if "location_tag" in gps_item:
                    combined_item["location_tag"] = gps_item["location_tag"]

                self.image_data.append(combined_item)

        return self.image_data

    def save_results(self, output_path: str = "clip_humanists_results.json"):
        """
        Save the results to a JSON file.

        Args:
            output_path: Path to save the results
        """
        if not self.image_data:
            raise ValueError("No image data to save. Run process_images first.")

        # Convert to a serializable format
        serializable_data = []
        for item in self.image_data:
            serialized_item = {
                "filepath": item["filepath"],
                "similarities": item["similarities"],
            }

            if item.get("gps_coordinates"):
                # Convert tuple to list for JSON serialization
                serialized_item["gps_coordinates"] = (
                    list(item["gps_coordinates"])
                    if isinstance(item["gps_coordinates"], tuple)
                    else item["gps_coordinates"]
                )

            if item.get("location_tag"):
                serialized_item["location_tag"] = item["location_tag"]

            serializable_data.append(serialized_item)

        with open(output_path, "w") as f:
            json.dump(serializable_data, f, indent=2)

        print(f"Results saved to {output_path}")

    def load_results(self, input_path: str):
        """
        Load results from a JSON file.

        Args:
            input_path: Path to the JSON file
        """
        with open(input_path, "r") as f:
            self.image_data = json.load(f)

        print(f"Loaded results from {input_path}")

    def create_similarity_heatmap(self, title: str = "Image-Text Similarity Heatmap"):
        """
        Create a heatmap of image-text similarities.

        Args:
            title: Title for the heatmap

        Returns:
            Matplotlib figure
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        # Convert to the format expected by plot_similarity_heatmap
        similarities = {
            item["filepath"]: item["similarities"] for item in self.image_data
        }

        return plot_similarity_heatmap(similarities, title)

    def create_map(
        self, center: Optional[Tuple[float, float]] = None, zoom_start: int = 13
    ):
        """
        Create a map with images at their GPS coordinates.

        Args:
            center: Center coordinates for the map
            zoom_start: Initial zoom level

        Returns:
            Folium map
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        return create_map_with_images(self.image_data, center, zoom_start)

    def create_similarity_by_location_plot(
        self,
        text_prompt: str,
        location_field: str = "location_tag",
        title: str = "Similarity Scores by Location",
    ):
        """
        Create a box plot of similarity scores grouped by location.

        Args:
            text_prompt: The text prompt to plot similarities for
            location_field: The field in image_data that contains location information
            title: Title for the plot

        Returns:
            Matplotlib figure
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        return plot_similarity_by_location(
            self.image_data, text_prompt, location_field, title
        )

    def create_image_grid(
        self,
        text_prompt: Optional[str] = None,
        cols: int = 3,
        figsize: Tuple[int, int] = (15, 15),
        title: str = "Image Grid",
    ):
        """
        Display a grid of images with optional similarity scores.

        Args:
            text_prompt: Optional text prompt to display similarity scores for
            cols: Number of columns in the grid
            figsize: Figure size
            title: Title for the grid

        Returns:
            Matplotlib figure
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        image_paths = [item["filepath"] for item in self.image_data]
        similarities = {
            item["filepath"]: item["similarities"] for item in self.image_data
        }

        return display_image_grid(
            image_paths, similarities, text_prompt, cols, figsize, title
        )

    def get_top_images_for_prompt(
        self, text_prompt: str, n: int = 5
    ) -> List[Dict[str, Union[str, float]]]:
        """
        Get the top n images for a given text prompt.

        Args:
            text_prompt: The text prompt to find top images for
            n: Number of top images to return

        Returns:
            List of dictionaries with filepath and similarity score
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        # Extract filepath and similarity score for the given prompt
        prompt_scores = [
            {"filepath": item["filepath"], "score": item["similarities"][text_prompt]}
            for item in self.image_data
            if text_prompt in item["similarities"]
        ]

        # Sort by score in descending order and take top n
        top_images = sorted(prompt_scores, key=lambda x: x["score"], reverse=True)[:n]

        return top_images

    def get_dataframe(self) -> pd.DataFrame:
        """
        Convert image data to a pandas DataFrame.

        Returns:
            Pandas DataFrame
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        # Create a list of dictionaries for the DataFrame
        df_data = []
        for item in self.image_data:
            row = {
                "filepath": item["filepath"],
                "filename": os.path.basename(item["filepath"]),
            }

            if item.get("gps_coordinates"):
                coords = item["gps_coordinates"]
                if isinstance(coords, list):
                    row["latitude"] = coords[0]
                    row["longitude"] = coords[1]
                else:
                    row["latitude"] = coords[0]
                    row["longitude"] = coords[1]

            if item.get("location_tag"):
                row["location_tag"] = item["location_tag"]

            # Add similarity scores
            for prompt, score in item["similarities"].items():
                row[f"similarity_{prompt}"] = score

            df_data.append(row)

        return pd.DataFrame(df_data)

    def create_image_similarity_bars(
        self,
        image_index: int = 0,
        output_dir: str = "result_images",
        figsize: Tuple[int, int] = (12, 6),
    ) -> str:
        """
        Create a visualization with an image and a bar graph of its similarity scores.

        Args:
            image_index: Index of the image in image_data
            output_dir: Directory to save the visualization
            figsize: Figure size

        Returns:
            Path to the saved visualization
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        if image_index >= len(self.image_data):
            raise ValueError(
                f"Image index {image_index} out of range (0-{len(self.image_data)-1})"
            )

        item = self.image_data[image_index]
        filepath = item["filepath"]
        similarities = item["similarities"]

        return create_image_with_similarity_bars(
            filepath, similarities, output_dir, figsize
        )

    def create_all_image_similarity_bars(
        self, output_dir: str = "result_images"
    ) -> List[str]:
        """
        Create visualizations for all images with their similarity scores.

        Args:
            output_dir: Directory to save the visualizations

        Returns:
            List of paths to the saved visualizations
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        return create_all_image_similarity_bars(self.image_data, output_dir)

    def create_similarity_correlation_matrix(
        self,
        figsize: Tuple[int, int] = (10, 8),
        title: str = "Correlation Between Concepts",
    ) -> plt.Figure:
        """
        Create a correlation matrix of similarity scores between different text prompts.

        Args:
            figsize: Figure size
            title: Title for the plot

        Returns:
            Matplotlib figure
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        return create_similarity_correlation_matrix(self.image_data, figsize, title)

    def normalize_coordinates(self) -> None:
        """
        Normalize GPS coordinates and add them to image_data.
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        self.image_data = normalize_coordinates(self.image_data)

    def cluster_locations(self, n_clusters: int = 3) -> None:
        """
        Cluster GPS coordinates and add cluster information to image_data.

        Args:
            n_clusters: Number of clusters to create
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        self.image_data = cluster_locations(self.image_data, n_clusters)

    def create_location_correlation_plot(
        self,
        text_prompt: str,
        figsize: Tuple[int, int] = (10, 8),
        title: Optional[str] = None,
    ) -> plt.Figure:
        """
        Create a scatter plot of normalized coordinates colored by similarity score.

        Args:
            text_prompt: The text prompt to plot similarities for
            figsize: Figure size
            title: Optional title for the plot

        Returns:
            Matplotlib figure
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        # Ensure coordinates are normalized
        if not any("normalized_coordinates" in item for item in self.image_data):
            self.normalize_coordinates()

        return create_location_correlation_plot(
            self.image_data, text_prompt, figsize, title
        )

    def calculate_location_similarity_correlation(
        self, text_prompts: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Calculate correlations between location and similarity scores.

        Args:
            text_prompts: List of text prompts to analyze. If None, use all available prompts.

        Returns:
            DataFrame with correlation statistics
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        # Ensure coordinates are normalized
        if not any("normalized_coordinates" in item for item in self.image_data):
            self.normalize_coordinates()

        # If no text prompts are provided, use all available prompts
        if text_prompts is None:
            # Get all unique prompts from the data
            all_prompts = set()
            for item in self.image_data:
                all_prompts.update(item["similarities"].keys())
            text_prompts = sorted(list(all_prompts))

        return calculate_location_similarity_correlation(self.image_data, text_prompts)

    def create_similarity_violin_plot(
        self,
        figsize: Tuple[int, int] = (12, 8),
        title: str = "Distribution of Similarity Scores",
    ) -> plt.Figure:
        """
        Create a violin plot showing the distribution of similarity scores for each text prompt.

        Args:
            figsize: Figure size
            title: Title for the plot

        Returns:
            Matplotlib figure
        """
        if not self.image_data:
            raise ValueError("No image data available. Run process_images first.")

        return create_similarity_violin_plot(self.image_data, figsize, title)
