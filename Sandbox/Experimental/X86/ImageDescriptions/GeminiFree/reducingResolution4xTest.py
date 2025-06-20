import google.generativeai as genai
from PIL import Image
from PIL import ImageOps
import os
import io
import time

genai.configure(api_key="AIzaSyB5-xHZz3q0Kv9LuhkdZjftzRWrAYts_pg")
model = genai.GenerativeModel("gemini-2.5-flash")

# Original image path
image_path = r"C:\Users\cicai\Desktop\20250122_131334.jpg"
prompt = "Describe what's happening in this image."

# Load original image and maintain orientation
original_img = Image.open(image_path)
original_img = ImageOps.exif_transpose(original_img)
descriptions = []



for i in range(4):
    # Resize image
    scale = 0.5 ** i
    new_width = max(1, int(original_img.width * scale))
    new_height = max(1, int(original_img.height * scale))
    resized_img = original_img.resize((new_width, new_height), Image.LANCZOS)

    # Save resized image to bytes
    img_byte_arr = io.BytesIO()
    resized_img.save(img_byte_arr, format='JPEG')
    image_bytes = img_byte_arr.getvalue()

    # Estimate image tokens
    tiles_w = (new_width + 767) // 768
    tiles_h = (new_height + 767) // 768
    image_tokens = tiles_w * tiles_h * 258

    # Estimate file size
    file_size_kb = len(image_bytes) / 1024

    # Estimate prompt tokens
    prompt_tokens = len(prompt) // 4

    # Measure response time
    start_time = time.perf_counter()
    response = model.generate_content([
        {"text": prompt},
        {"inline_data": {"mime_type": "image/jpeg", "data": image_bytes}}
    ])
    end_time = time.perf_counter()
    response_time = end_time - start_time

    # Estimate response tokens
    response_text = response.text.strip()
    response_tokens = len(response_text) // 4

    # Store result
    descriptions.append({
        "iteration": i + 1,
        "dimensions": f"{new_width}x{new_height}",
        "file_size_kb": file_size_kb,
        "description": response_text,
        "tokens": {
            "prompt": prompt_tokens,
            "image": image_tokens,
            "response": response_tokens,
            "total": prompt_tokens + image_tokens + response_tokens
        },
        "response_time": response_time
    })

# Print results
for desc in descriptions:
    print(f"\n--- Description {desc['iteration']} ---")
    print(f"Image resolution: {desc['dimensions']}")
    print(f"Image file size: {desc['file_size_kb']:.2f} KB")
    print(f"Response time: {desc['response_time']:.2f} seconds")
    print(f"Description: {desc['description']}")
    print("\nToken Estimate:")
    print(f"  Prompt tokens: {desc['tokens']['prompt']}")
    print(f"  Image tokens: {desc['tokens']['image']}")
    print(f"  Response tokens: {desc['tokens']['response']}")
    print(f"  Total estimated tokens: {desc['tokens']['total']}")