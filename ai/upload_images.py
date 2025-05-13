import cloudinary
import cloudinary.uploader
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from tqdm import tqdm

# === Cloudinary config ===
cloudinary.config(
    cloud_name="dommjhw2e",
    api_key="474542799276528",
    api_secret="3ZkIKMhGtYYYn8yBoTdmvpqiIjI"
)

# === Paths ===
dataset_path = r"F:\Documents\Assignment\7\ecochef\ai\cleaned_recipes.csv"
image_folder = r"F:\Documents\Assignment\7\Dataset\Food_Images"
compressed_folder = r"F:\Documents\Assignment\7\Dataset\Compressed"
output_path = r"F:\Documents\Assignment\7\ecochef\ai\cleaned_recipes_with_urls.csv"
error_log_path = r"F:\Documents\Assignment\7\ecochef\ai\upload_errors.txt"

# Ensure compressed image directory exists
os.makedirs(compressed_folder, exist_ok=True)

# Load dataset and reset URLs
df = pd.read_csv(dataset_path)
df["Image_URL"] = ""

# === Compress ===
def compress_image(image_name, quality=80):
    original_path = os.path.join(image_folder, f"{image_name}.jpg")
    compressed_path = os.path.join(compressed_folder, f"{image_name}.jpg")
    try:
        img = Image.open(original_path).convert("RGB")
        img.save(compressed_path, "JPEG", optimize=True, quality=quality)
        return compressed_path
    except Exception as e:
        with open(error_log_path, "a") as f:
            f.write(f"Compression error for {image_name}: {e}\n")
        return None

# === Upload ===
def upload_image(index, image_name):
    try:
        path = compress_image(image_name)
        if path and os.path.exists(path):
            result = cloudinary.uploader.upload(
                path,
                public_id=image_name,
                overwrite=True,
                transformation={"width": 512, "height": 512, "crop": "limit"}
            )
            return result["secure_url"]
    except Exception as e:
        with open(error_log_path, "a") as f:
            f.write(f"Upload error for {image_name}: {e}\n")
    return ""

# === Parallel Upload ===
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {
        executor.submit(upload_image, idx, row["Image_Name"]): idx
        for idx, row in df.iterrows()
    }
    for future in tqdm(as_completed(futures), total=len(futures), desc="Uploading"):
        idx = futures[future]
        df.at[idx, "Image_URL"] = future.result()

# === Save ===
df.to_csv(output_path, index=False)
print("Upload complete! All images refreshed.") 