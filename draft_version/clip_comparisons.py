import os
import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import geopy.distance
import torch

from torchvision import transforms
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm


# Function to extract GPS coordinates from an image
def get_gps_coordinates(img_path):
    image = Image.open(img_path)
    info = image._getexif()
    if info is None:
        return None

    gps_info = {}
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            for t in value:
                sub_decoded = GPSTAGS.get(t, t)
                gps_info[sub_decoded] = value[t]

    if not gps_info:
        return None

    def get_if_exist(data, key):
        return data.get(key)

    def convert_to_degrees(value):
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)

    lat = None
    lon = None

    gps_latitude = get_if_exist(gps_info, "GPSLatitude")
    gps_latitude_ref = get_if_exist(gps_info, "GPSLatitudeRef")
    gps_longitude = get_if_exist(gps_info, "GPSLongitude")
    gps_longitude_ref = get_if_exist(gps_info, "GPSLongitudeRef")

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = convert_to_degrees(gps_latitude)
        if gps_latitude_ref != "N":
            lat = 0 - lat

        lon = convert_to_degrees(gps_longitude)
        if gps_longitude_ref != "E":
            lon = 0 - lon

    return (lat, lon)


# Define the dictionary with place names and coordinates
location_dict = {
    "place_1": (40.748817, -73.985428),  # Example: New York
    "place_2": (34.052235, -118.243683),  # Example: Los Angeles
    # Add more places as needed
}


# Function to find the closest location tag
def get_closest_location_tag(gps_coords, location_dict):
    if gps_coords is None:
        return None

    closest_location = None
    min_distance = float("inf")

    for place, coords in tqdm(location_dict.items(), desc="Finding closest location"):
        distance = geopy.distance.distance(gps_coords, coords).km
        if distance < min_distance:
            min_distance = distance
            closest_location = place

    return closest_location


# List all jpg files in the folder
folder_path = "../../DogSignsOfVanttila/raw_img/"
jpg_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]

# Create a dataframe
data = []
for jpg_file in tqdm(jpg_files, desc="Extracting GPS coordinates"):
    file_path = os.path.join(folder_path, jpg_file)
    gps_coords = get_gps_coordinates(file_path)
    location_tag = get_closest_location_tag(gps_coords, location_dict)
    data.append((file_path, gps_coords, location_tag))

df = pd.DataFrame(data, columns=["filepath", "gps_coordinates", "location_tag"])

# Load CLIP model
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


# Comparison list
comparison_list = [
    "scary",
    "friendly",
    "dog",
    "threat",
    "warning",
    "information",
    "signs",
]

# Prepare comparison texts
text_inputs = processor(text=comparison_list, return_tensors="pt", padding=True).to(
    device
)


# Add similarity scores to dataframe
similarity_data = []

for jpg_file in tqdm(jpg_files, desc="Calculating similarities"):
    file_path = os.path.join(folder_path, jpg_file)
    image = Image.open(file_path)
    image_input = processor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        image_features = model.get_image_features(**image_input)
        text_features = model.get_text_features(**text_inputs)

    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    similarities = (image_features @ text_features.T).squeeze().cpu().numpy()

    similarity_data.append(similarities)

# Convert similarity data to DataFrame and add to original DataFrame
similarity_df = pd.DataFrame(
    similarity_data, columns=[f"comparison_value__{name}" for name in comparison_list]
)
df = pd.concat([df, similarity_df], axis=1)

# Display the dataframe
# import ace_tools as tools

# tools.display_dataframe_to_user(
#    name="Image GPS and CLIP Comparison DataFrame", dataframe=df
# )

# Save the dataframe to a JSON file
df.to_json("image_gps_clip_data.json", orient="records")
