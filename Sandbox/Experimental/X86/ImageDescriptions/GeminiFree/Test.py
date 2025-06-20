import google.generativeai as genai
from PIL import Image
import os

genai.configure(api_key="AIzaSyB5-xHZz3q0Kv9LuhkdZjftzRWrAYts_pg")
model = genai.GenerativeModel("gemini-2.0-flash")

# Load image and get dimensions + file size
image_path = r"C:\Users\cicai\Desktop\20250122_131334.jpg"
with open(image_path, "rb") as f:
    image_bytes = f.read()

# Get image dimensions
with Image.open(image_path) as img:
    width, height = img.size

# Estimate image tokens (1 tile = 768x768 = 258 tokens)
tiles_w = (width + 767) // 768
tiles_h = (height + 767) // 768
image_tokens = tiles_w * tiles_h * 258

# Estimate file size in KB
file_size_kb = os.path.getsize(image_path) / 1024

# Prompt and token estimates
prompt = "Describe what's happening in this image."
prompt_tokens = len(prompt) // 4

response = model.generate_content([
    {"text": prompt},
    {"inline_data": {"mime_type": "image/jpeg", "data": image_bytes}}
])

response_text = response.text
response_tokens = len(response_text) // 4

# Output
print(response_text)
print("\n--- Token Usage Estimate ---")
print(f"Image dimensions: {width}x{height}")
print(f"Image file size: {file_size_kb:.2f} KB")
print(f"Prompt tokens: {prompt_tokens}")
print(f"Image tokens (estimated): {image_tokens}")
print(f"Response tokens (estimated): {response_tokens}")
print(f"Total estimated tokens: {prompt_tokens + image_tokens + response_tokens}")