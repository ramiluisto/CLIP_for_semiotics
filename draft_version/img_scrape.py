import os
import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import geopy.distance


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

    for place, coords in location_dict.items():
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
for jpg_file in jpg_files:
    file_path = os.path.join(folder_path, jpg_file)
    gps_coords = get_gps_coordinates(file_path)
    location_tag = get_closest_location_tag(gps_coords, location_dict)
    data.append((file_path, gps_coords, location_tag))

df = pd.DataFrame(data, columns=["filepath", "gps_coordinates", "location_tag"])
df.to_json("image_gps_data.json", orient="records")
# Display the dataframe
# import ace_tools as tools; tools.display_dataframe_to_user(name="Image GPS DataFrame", dataframe=df)
