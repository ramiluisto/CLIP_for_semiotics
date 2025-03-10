#!/usr/bin/env python
"""
Script to resize images while preserving EXIF metadata.
"""

import os
import shutil
from PIL import Image
import piexif
from pathlib import Path
import tempfile


def resize_image_preserve_exif(input_path, output_path, max_size=800):
    """
    Resize an image while preserving its EXIF metadata.

    Args:
        input_path: Path to input image
        output_path: Path to save resized image
        max_size: Maximum dimension (width or height) for the resized image
    """
    # Open the image
    img = Image.open(input_path)

    # Extract EXIF data if present
    exif_data = None
    if "exif" in img.info:
        exif_data = img.info["exif"]

    # Calculate new dimensions
    width, height = img.size
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))

    # Resize the image
    resized_img = img.resize((new_width, new_height), Image.LANCZOS)

    # Save with EXIF data if it existed
    if exif_data:
        resized_img.save(output_path, exif=exif_data)
    else:
        resized_img.save(output_path)

    print(
        f"Resized {os.path.basename(input_path)} from {width}x{height} to {new_width}x{new_height}"
    )


def process_image_folder(folder_path, num_images=3, max_size=800):
    """
    Process an image folder by keeping only a specified number of images and resizing them.

    Args:
        folder_path: Path to the folder containing images
        num_images: Number of images to keep
        max_size: Maximum dimension for resized images
    """
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist.")
        return

    # List all jpg files
    image_files = [
        f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg"))
    ]
    image_files.sort()  # Sort alphabetically

    # Keep only the specified number of images
    images_to_keep = image_files[:num_images]
    images_to_remove = [f for f in image_files if f not in images_to_keep]

    print(f"Processing folder: {folder_path}")
    print(f"Keeping {len(images_to_keep)} images: {', '.join(images_to_keep)}")
    print(f"Removing {len(images_to_remove)} images")

    # Create a temporary directory for resized images
    with tempfile.TemporaryDirectory() as temp_dir:
        # Resize images to keep
        for img_file in images_to_keep:
            input_path = os.path.join(folder_path, img_file)
            temp_output_path = os.path.join(temp_dir, img_file)
            resize_image_preserve_exif(input_path, temp_output_path, max_size)

        # Remove all original images
        for img_file in image_files:
            os.remove(os.path.join(folder_path, img_file))

        # Copy resized images back
        for img_file in images_to_keep:
            shutil.copy2(
                os.path.join(temp_dir, img_file), os.path.join(folder_path, img_file)
            )

    print(f"Completed processing {folder_path}")


if __name__ == "__main__":
    # Process main image folder
    process_image_folder("img", num_images=3, max_size=800)

    # Process example_img folder if it exists
    if os.path.exists("example_img"):
        process_image_folder("example_img", num_images=3, max_size=800)

    print("Image processing complete.")
