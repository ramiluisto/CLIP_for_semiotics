"""
Utilities for visualizing image analysis results.
"""

from typing import Dict, List, Optional, Tuple, Union
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import folium
from PIL import Image
import base64
from io import BytesIO
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy import stats


def plot_similarity_heatmap(
    similarities: Dict[str, Dict[str, float]],
    title: str = "Image-Text Similarity Heatmap",
) -> plt.Figure:
    """
    Create a heatmap of image-text similarities.

    Args:
        similarities: Dictionary mapping image paths to dictionaries of text-similarity pairs
        title: Title for the heatmap

    Returns:
        Matplotlib figure
    """
    # Extract image filenames and text prompts
    image_names = [os.path.basename(img_path) for img_path in similarities.keys()]
    if not image_names:
        raise ValueError("No images to plot")

    # Get text prompts from the first image (assuming all images have the same prompts)
    first_image = list(similarities.keys())[0]
    text_prompts = list(similarities[first_image].keys())

    # Create a matrix of similarity scores
    similarity_matrix = np.zeros((len(image_names), len(text_prompts)))
    for i, img_path in enumerate(similarities.keys()):
        for j, prompt in enumerate(text_prompts):
            similarity_matrix[i, j] = similarities[img_path][prompt]

    # Create the heatmap
    fig, ax = plt.subplots(figsize=(12, len(image_names) * 0.4 + 2))
    im = ax.imshow(similarity_matrix, cmap="viridis")

    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Similarity Score", rotation=-90, va="bottom")

    # Set ticks and labels
    ax.set_xticks(np.arange(len(text_prompts)))
    ax.set_yticks(np.arange(len(image_names)))
    ax.set_xticklabels(text_prompts)
    ax.set_yticklabels(image_names)

    # Rotate the x-axis labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Add title and adjust layout
    ax.set_title(title)
    fig.tight_layout()

    return fig


def create_map_with_images(
    image_data: List[Dict[str, Union[str, Tuple[float, float]]]],
    center: Optional[Tuple[float, float]] = None,
    zoom_start: int = 13,
    width: int = 150,
    height: int = 150,
) -> folium.Map:
    """
    Create a folium map with images at their GPS coordinates.

    Args:
        image_data: List of dictionaries with filepath and gps_coordinates
        center: Center coordinates for the map (if None, will use the mean of all coordinates)
        zoom_start: Initial zoom level
        width: Width of the image thumbnails
        height: Height of the image thumbnails

    Returns:
        Folium map
    """
    # Filter out images without GPS coordinates
    valid_images = [img for img in image_data if img.get("gps_coordinates") is not None]

    if not valid_images:
        raise ValueError("No images with valid GPS coordinates")

    # Calculate center if not provided
    if center is None:
        lats = [img["gps_coordinates"][0] for img in valid_images]
        lons = [img["gps_coordinates"][1] for img in valid_images]
        center = (np.mean(lats), np.mean(lons))

    # Create map
    m = folium.Map(location=center, zoom_start=zoom_start)

    # Add markers with images
    for img_data in valid_images:
        filepath = img_data["filepath"]
        coords = img_data["gps_coordinates"]

        # Create thumbnail
        image = Image.open(filepath)
        image.thumbnail((width, height))

        # Convert image to base64 for embedding in HTML
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Create HTML for the popup
        html = f'<img src="data:image/jpeg;base64,{img_str}"><br>{os.path.basename(filepath)}'

        # Add marker
        folium.Marker(
            location=coords,
            popup=folium.Popup(html, max_width=width + 20),
            tooltip=os.path.basename(filepath),
        ).add_to(m)

    return m


def plot_similarity_by_location(
    image_data: List[Dict[str, Union[str, Tuple[float, float], Dict[str, float]]]],
    text_prompt: str,
    location_field: str = "location_tag",
    title: str = "Similarity Scores by Location",
) -> plt.Figure:
    """
    Create a box plot of similarity scores grouped by location.

    Args:
        image_data: List of dictionaries with similarities and location information
        text_prompt: The text prompt to plot similarities for
        location_field: The field in image_data that contains location information
        title: Title for the plot

    Returns:
        Matplotlib figure
    """
    # Filter out images without location information
    valid_images = [
        img
        for img in image_data
        if location_field in img and img[location_field] is not None
    ]

    if not valid_images:
        raise ValueError(f"No images with valid {location_field} information")

    # Extract locations and similarity scores
    locations = [img[location_field] for img in valid_images]
    scores = [img["similarities"][text_prompt] for img in valid_images]

    # Create DataFrame
    df = pd.DataFrame({"Location": locations, "Similarity": scores})

    # Group by location
    grouped = df.groupby("Location")["Similarity"].apply(list).to_dict()

    # Create box plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(grouped.values(), labels=grouped.keys())

    # Add labels and title
    ax.set_xlabel("Location")
    ax.set_ylabel(f"Similarity Score for '{text_prompt}'")
    ax.set_title(title)

    # Rotate x-axis labels if needed
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    fig.tight_layout()
    return fig


def display_image_grid(
    image_paths: List[str],
    similarities: Optional[Dict[str, Dict[str, float]]] = None,
    text_prompt: Optional[str] = None,
    cols: int = 3,
    figsize: Tuple[int, int] = (15, 15),
    title: str = "Image Grid",
) -> plt.Figure:
    """
    Display a grid of images with optional similarity scores.

    Args:
        image_paths: List of paths to images
        similarities: Optional dictionary mapping image paths to dictionaries of text-similarity pairs
        text_prompt: Optional text prompt to display similarity scores for
        cols: Number of columns in the grid
        figsize: Figure size
        title: Title for the grid

    Returns:
        Matplotlib figure
    """
    # Calculate number of rows needed
    n_images = len(image_paths)
    rows = (n_images + cols - 1) // cols

    # Create figure
    fig = plt.figure(figsize=figsize)
    fig.suptitle(title, fontsize=16)

    # Add images to grid
    for i, img_path in enumerate(image_paths):
        # Create subplot
        ax = fig.add_subplot(rows, cols, i + 1)

        # Display image
        try:
            img = Image.open(img_path)
            ax.imshow(img)

            # Add similarity score if provided
            if similarities and text_prompt:
                if img_path in similarities and text_prompt in similarities[img_path]:
                    score = similarities[img_path][text_prompt]
                    ax.set_title(f"{os.path.basename(img_path)}\nScore: {score:.3f}")
                else:
                    ax.set_title(os.path.basename(img_path))
            else:
                ax.set_title(os.path.basename(img_path))

            # Remove axis ticks
            ax.set_xticks([])
            ax.set_yticks([])

        except Exception as e:
            print(f"Error displaying image {img_path}: {e}")
            ax.text(
                0.5,
                0.5,
                f"Error loading\n{os.path.basename(img_path)}",
                ha="center",
                va="center",
            )
            ax.set_xticks([])
            ax.set_yticks([])

    fig.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust for the suptitle
    return fig


def create_image_with_similarity_bars(
    image_path: str,
    similarities: Dict[str, float],
    output_dir: str = "result_images",
    figsize: Tuple[int, int] = (12, 6),
    title: Optional[str] = None,
) -> str:
    """
    Create a visualization with an image and a bar graph of its similarity scores.

    Args:
        image_path: Path to the image
        similarities: Dictionary mapping text prompts to similarity scores
        output_dir: Directory to save the visualization
        figsize: Figure size
        title: Optional title for the plot

    Returns:
        Path to the saved visualization
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Sort text prompts by similarity score in descending order
    sorted_items = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    prompts = [item[0] for item in sorted_items]
    scores = [item[1] for item in sorted_items]

    # Create a figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=figsize, gridspec_kw={"width_ratios": [1, 1.5]}
    )

    # Plot the image on the left
    try:
        img = Image.open(image_path)
        ax1.imshow(img)
        ax1.set_title(os.path.basename(image_path))
        ax1.axis("off")
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        ax1.text(
            0.5,
            0.5,
            f"Error loading\n{os.path.basename(image_path)}",
            ha="center",
            va="center",
        )
        ax1.axis("off")

    # Plot the bar graph on the right
    colors = plt.cm.viridis(np.linspace(0, 1, len(prompts)))
    bars = ax2.barh(prompts, scores, color=colors)

    # Add values to the bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax2.text(
            width + 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.3f}",
            ha="left",
            va="center",
        )

    # Set limits for the bar graph
    ax2.set_xlim([-0.2, 1.0])

    # Set labels and title
    ax2.set_xlabel("Similarity Score")
    ax2.set_title("Similarity Scores by Concept")

    # Add overall title if provided
    if title:
        fig.suptitle(title, fontsize=16)
        fig.tight_layout(rect=[0, 0, 1, 0.96])
    else:
        fig.tight_layout()

    # Save the figure
    output_path = os.path.join(
        output_dir,
        f"{os.path.splitext(os.path.basename(image_path))[0]}_similarity.png",
    )
    fig.savefig(output_path)
    plt.close(fig)

    return output_path


def create_all_image_similarity_bars(
    image_data: List[Dict[str, Union[str, Dict[str, float]]]],
    output_dir: str = "result_images",
) -> List[str]:
    """
    Create visualizations for all images with their similarity scores.

    Args:
        image_data: List of dictionaries with filepath and similarities
        output_dir: Directory to save the visualizations

    Returns:
        List of paths to the saved visualizations
    """
    output_paths = []

    for item in image_data:
        filepath = item["filepath"]
        similarities = item["similarities"]

        output_path = create_image_with_similarity_bars(
            filepath, similarities, output_dir
        )
        output_paths.append(output_path)

    return output_paths


def create_similarity_correlation_matrix(
    image_data: List[Dict[str, Dict[str, float]]],
    figsize: Tuple[int, int] = (10, 8),
    title: str = "Correlation Between Concepts",
) -> plt.Figure:
    """
    Create a correlation matrix of similarity scores between different text prompts.

    Args:
        image_data: List of dictionaries with similarities
        figsize: Figure size
        title: Title for the plot

    Returns:
        Matplotlib figure
    """
    # Extract all unique prompts from the data
    all_prompts = set()
    for item in image_data:
        all_prompts.update(item["similarities"].keys())

    all_prompts = sorted(list(all_prompts))

    # Create a DataFrame with similarity scores for each prompt
    data = []
    for item in image_data:
        row = {}
        for prompt in all_prompts:
            if prompt in item["similarities"]:
                row[prompt] = item["similarities"][prompt]
            else:
                row[prompt] = np.nan
        data.append(row)

    df = pd.DataFrame(data)

    # Calculate correlation matrix
    corr_matrix = df.corr()

    # Create the heatmap
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(corr_matrix, cmap="coolwarm", vmin=-1, vmax=1)

    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Correlation", rotation=-90, va="bottom")

    # Set ticks and labels
    ax.set_xticks(np.arange(len(all_prompts)))
    ax.set_yticks(np.arange(len(all_prompts)))
    ax.set_xticklabels(all_prompts)
    ax.set_yticklabels(all_prompts)

    # Rotate the x-axis labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Add correlation values to the cells
    for i in range(len(all_prompts)):
        for j in range(len(all_prompts)):
            value = corr_matrix.iloc[i, j]
            if not np.isnan(value):
                text_color = "white" if abs(value) > 0.5 else "black"
                ax.text(
                    j, i, f"{value:.2f}", ha="center", va="center", color=text_color
                )

    # Add title and adjust layout
    ax.set_title(title)
    fig.tight_layout()

    return fig


def normalize_coordinates(
    image_data: List[Dict[str, Union[str, Tuple[float, float]]]],
) -> List[Dict[str, Union[str, Tuple[float, float], Tuple[float, float]]]]:
    """
    Normalize GPS coordinates to a 0-1 scale.

    Args:
        image_data: List of dictionaries with filepath and gps_coordinates

    Returns:
        List of dictionaries with normalized GPS coordinates added
    """
    # Filter out images without GPS coordinates
    valid_images = [img for img in image_data if img.get("gps_coordinates") is not None]

    if not valid_images:
        raise ValueError("No images with valid GPS coordinates")

    # Extract latitudes and longitudes
    lats = [img["gps_coordinates"][0] for img in valid_images]
    lons = [img["gps_coordinates"][1] for img in valid_images]

    # Calculate min and max values
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Calculate ranges
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon

    # Avoid division by zero if all points have the same coordinate
    lat_range = lat_range if lat_range > 0 else 1.0
    lon_range = lon_range if lon_range > 0 else 1.0

    # Normalize coordinates
    result = []
    for img in image_data:
        img_copy = img.copy()

        if img.get("gps_coordinates") is not None:
            lat, lon = img["gps_coordinates"]
            norm_lat = (lat - min_lat) / lat_range
            norm_lon = (lon - min_lon) / lon_range
            img_copy["normalized_coordinates"] = (norm_lat, norm_lon)

        result.append(img_copy)

    return result


def cluster_locations(
    image_data: List[Dict[str, Union[str, Tuple[float, float]]]], n_clusters: int = 3
) -> List[Dict[str, Union[str, Tuple[float, float], int]]]:
    """
    Cluster GPS coordinates using KMeans.

    Args:
        image_data: List of dictionaries with filepath and gps_coordinates
        n_clusters: Number of clusters to create

    Returns:
        List of dictionaries with location clusters added
    """
    # Filter out images without GPS coordinates
    valid_images = [img for img in image_data if img.get("gps_coordinates") is not None]

    if not valid_images:
        raise ValueError("No images with valid GPS coordinates")

    # Extract coordinates
    coords = np.array([list(img["gps_coordinates"]) for img in valid_images])

    # Standardize the coordinates
    scaler = StandardScaler()
    scaled_coords = scaler.fit_transform(coords)

    # Perform KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(scaled_coords)

    # Add cluster information to valid images
    for i, img in enumerate(valid_images):
        img["location_cluster"] = int(clusters[i])

    # Add cluster information to all images
    result = []
    for img in image_data:
        if img.get("gps_coordinates") is not None:
            # This image was in valid_images and already has the cluster
            result.append(img)
        else:
            # This image was not in valid_images
            img_copy = img.copy()
            result.append(img_copy)

    return result


def create_location_correlation_plot(
    image_data: List[Dict[str, Union[str, Tuple[float, float], Dict[str, float], int]]],
    text_prompt: str,
    figsize: Tuple[int, int] = (10, 12),
    title: Optional[str] = None,
) -> plt.Figure:
    """
    Create a plot showing the correlation between location coordinates and similarity scores.

    Args:
        image_data: List of dictionaries with normalized_coordinates, similarities, and location_cluster
        text_prompt: The text prompt to plot similarities for
        figsize: Figure size
        title: Optional title for the plot

    Returns:
        Matplotlib figure
    """
    # Filter out images without normalized coordinates or similarities
    valid_images = [
        img
        for img in image_data
        if img.get("normalized_coordinates") is not None
        and "similarities" in img
        and text_prompt in img["similarities"]
    ]

    if not valid_images:
        raise ValueError("No images with valid normalized coordinates and similarities")

    # Extract data
    norm_lats = [img["normalized_coordinates"][0] for img in valid_images]
    norm_lons = [img["normalized_coordinates"][1] for img in valid_images]
    scores = [img["similarities"][text_prompt] for img in valid_images]

    # Create figure with 2 subplots stacked vertically
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)

    # Scatter plot for latitude vs similarity
    ax1.scatter(norm_lats, scores, c=scores, cmap="viridis", s=80, alpha=0.7)
    ax1.set_xlabel("Normalized Latitude")
    ax1.set_ylabel(f"Similarity Score for '{text_prompt}'")

    # Calculate and display correlation coefficient
    lat_corr, lat_p = stats.pearsonr(norm_lats, scores)
    lat_correlation_text = f"Correlation: {lat_corr:.3f}\np-value: {lat_p:.3f}"
    ax1.text(
        0.05,
        0.95,
        lat_correlation_text,
        transform=ax1.transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.7),
    )

    # Add trend line for latitude correlation
    lat_z = np.polyfit(norm_lats, scores, 1)
    lat_p = np.poly1d(lat_z)
    ax1.plot(norm_lats, lat_p(norm_lats), "r--", alpha=0.7)

    # Scatter plot for longitude vs similarity
    ax2.scatter(norm_lons, scores, c=scores, cmap="viridis", s=80, alpha=0.7)
    ax2.set_xlabel("Normalized Longitude")
    ax2.set_ylabel(f"Similarity Score for '{text_prompt}'")

    # Calculate and display correlation coefficient
    lon_corr, lon_p = stats.pearsonr(norm_lons, scores)
    lon_correlation_text = f"Correlation: {lon_corr:.3f}\np-value: {lon_p:.3f}"
    ax2.text(
        0.05,
        0.95,
        lon_correlation_text,
        transform=ax2.transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.7),
    )

    # Add trend line for longitude correlation
    lon_z = np.polyfit(norm_lons, scores, 1)
    lon_p = np.poly1d(lon_z)
    ax2.plot(norm_lons, lon_p(norm_lons), "r--", alpha=0.7)

    # Add annotations for image names
    for i, img in enumerate(valid_images):
        # Annotate in the latitude plot
        ax1.annotate(
            os.path.basename(img["filepath"]),
            (norm_lats[i], scores[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=7,
            alpha=0.7,
        )

        # Annotate in the longitude plot
        ax2.annotate(
            os.path.basename(img["filepath"]),
            (norm_lons[i], scores[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=7,
            alpha=0.7,
        )

    # Set grid
    ax1.grid(True, linestyle="--", alpha=0.7)
    ax2.grid(True, linestyle="--", alpha=0.7)

    # Set title
    if title:
        fig.suptitle(title, fontsize=14)
    else:
        fig.suptitle(
            f"Correlation between Location and Similarity for '{text_prompt}'",
            fontsize=14,
        )

    fig.tight_layout()
    return fig


def calculate_location_similarity_correlation(
    image_data: List[Dict[str, Union[str, Tuple[float, float], Dict[str, float]]]],
    text_prompts: List[str],
) -> pd.DataFrame:
    """
    Calculate correlations between location and similarity scores.

    Args:
        image_data: List of dictionaries with normalized_coordinates and similarities
        text_prompts: List of text prompts to analyze

    Returns:
        DataFrame with correlation statistics
    """
    # Filter out images without normalized coordinates
    valid_images = [
        img for img in image_data if img.get("normalized_coordinates") is not None
    ]

    if not valid_images:
        raise ValueError("No images with valid normalized coordinates")

    # Prepare results
    results = []

    for prompt in text_prompts:
        # Filter images that have this prompt
        prompt_images = [img for img in valid_images if prompt in img["similarities"]]

        if not prompt_images:
            continue

        # Extract data
        norm_lats = [img["normalized_coordinates"][0] for img in prompt_images]
        norm_lons = [img["normalized_coordinates"][1] for img in prompt_images]
        scores = [img["similarities"][prompt] for img in prompt_images]

        # Calculate correlations with latitude
        lat_corr, lat_p = stats.pearsonr(norm_lats, scores)

        # Calculate correlations with longitude
        lon_corr, lon_p = stats.pearsonr(norm_lons, scores)

        # Store results
        results.append(
            {
                "prompt": prompt,
                "latitude_correlation": lat_corr,
                "latitude_p_value": lat_p,
                "longitude_correlation": lon_corr,
                "longitude_p_value": lon_p,
                "n_samples": len(prompt_images),
            }
        )

    return pd.DataFrame(results)


def create_similarity_violin_plot(
    image_data: List[Dict[str, Dict[str, float]]],
    figsize: Tuple[int, int] = (12, 8),
    title: str = "Distribution of Similarity Scores",
) -> plt.Figure:
    """
    Create a violin plot showing the distribution of similarity scores for each text prompt.

    Args:
        image_data: List of dictionaries with similarities
        figsize: Figure size
        title: Title for the plot

    Returns:
        Matplotlib figure
    """
    # Extract all unique prompts
    all_prompts = set()
    for img in image_data:
        if "similarities" in img:
            all_prompts.update(img["similarities"].keys())

    all_prompts = sorted(list(all_prompts))

    if not all_prompts:
        raise ValueError("No text prompts found in the image data")

    # Prepare data for violin plot
    data_dict = {prompt: [] for prompt in all_prompts}

    for img in image_data:
        if "similarities" in img:
            for prompt in all_prompts:
                if prompt in img["similarities"]:
                    data_dict[prompt].append(img["similarities"][prompt])

    # Create the figure
    fig, ax = plt.subplots(figsize=figsize)

    # Create violin plot
    violin_parts = ax.violinplot(
        [data_dict[prompt] for prompt in all_prompts],
        showmeans=True,
        showmedians=True,
        showextrema=True,
    )

    # Change violin fill colors
    for i, pc in enumerate(violin_parts["bodies"]):
        pc.set_facecolor(plt.cm.viridis(i / len(all_prompts)))
        pc.set_edgecolor("black")
        pc.set_alpha(0.7)

    # Customize plot appearance
    ax.set_xticks(np.arange(1, len(all_prompts) + 1))
    ax.set_xticklabels(all_prompts, rotation=45, ha="right")
    ax.set_ylabel("Similarity Score")
    ax.set_title(title)

    # Add grid lines for better readability
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)

    # Add statistical annotations
    means = [np.mean(data_dict[prompt]) for prompt in all_prompts]
    medians = [np.median(data_dict[prompt]) for prompt in all_prompts]

    # Add a table with statistics below the plot
    stats_table = pd.DataFrame(
        {
            "Prompt": all_prompts,
            "Mean": means,
            "Median": medians,
            "Min": [min(data_dict[prompt]) for prompt in all_prompts],
            "Max": [max(data_dict[prompt]) for prompt in all_prompts],
            "Count": [len(data_dict[prompt]) for prompt in all_prompts],
        }
    )

    # Create a string representation of the table for the text box
    table_text = "Statistics:\n"
    for i, prompt in enumerate(all_prompts):
        table_text += f"{prompt}: mean={means[i]:.3f}, median={medians[i]:.3f}\n"

    # Add text box with statistics
    ax.text(
        0.5,
        -0.2,
        table_text,
        transform=ax.transAxes,
        fontsize=9,
        ha="center",
        va="center",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    fig.tight_layout()
    return fig
