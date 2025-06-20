import ollama
import json
import time
import os
from PIL import Image

# Image file path
image_path = 'XnRmqt5.jpg'

# To store metrics
metrics = []

# Function to process the image with the model
def process_image(image, description):
    start_time = time.time()
    temp_image_path = 'temp_image.jpg'
    image.save(temp_image_path)
    file_size = os.path.getsize(temp_image_path) / 1024  # Convert to KB
    response = ollama.chat(
        model='llama3.2-vision',
        messages=[{
            'role': 'user',
            'content': f'What is in this image? ({description})',
            'images': [temp_image_path]
        }]
    )
    end_time = time.time()
    execution_time = end_time - start_time

    # Calculate word count of the message content
    word_count = len(response.message.content.split())

    # Store metrics
    metrics.append((description, execution_time, file_size, word_count))

    print(f"\n--- Processing {description} ---")
    print(f"Image Description: {description}")
    pretty_print_response(response)
    print(f"Execution Time: {execution_time:.2f} seconds")
    print(f"File Size: {file_size:.2f} KB")
    print(f"Description Word Count: {word_count}")

# Extracting and formatting the response
def pretty_print_response(response):
    print("\n--- Llama 3.2 Vision Response ---\n")
    print(f"**Model**: {response.model}")
    print(f"**Created At**: {response.created_at}")
    print(f"**Done**: {response.done}")
    print(f"**Done Reason**: {response.done_reason}")
    print(f"**Total Duration**: {response.total_duration} ns")
    print(f"**Load Duration**: {response.load_duration} ns")
    print(f"**Prompt Eval Count**: {response.prompt_eval_count}")
    print(f"**Prompt Eval Duration**: {response.prompt_eval_duration} ns")
    print(f"**Eval Count**: {response.eval_count}")
    print(f"**Eval Duration**: {response.eval_duration} ns")
    print("\n**Message**:\n")
    formatted_message = "\n".join([line.strip() + '.' for line in response.message.content.split('.') if line.strip()])
    print(formatted_message)

# Load the original image
original_image = Image.open(image_path)

# 1. Process the original image (normal)
process_image(original_image, "Original Image")

# 2. Process the image in black and white
grayscale_image = original_image.convert('L')
process_image(grayscale_image, "Black and White Image")

# 3. Process the image at 50% resolution
half_res_image = original_image.resize(
    (original_image.width // 2, original_image.height // 2), Image.Resampling.LANCZOS
)
process_image(half_res_image, "Half Resolution Image")

# 4. Process the image at 50% resolution in black and white
half_res_grayscale_image = grayscale_image.resize(
    (grayscale_image.width // 2, grayscale_image.height // 2), Image.Resampling.LANCZOS
)
process_image(half_res_grayscale_image, "Half Resolution Black and White Image")

# 5. Optional: Experiment with high JPEG compression
compressed_image_path = 'compressed_image.jpg'
original_image.save(compressed_image_path, 'JPEG', quality=10)
compressed_image = Image.open(compressed_image_path)
process_image(compressed_image, "Highly Compressed Image")

# Display metrics as a tier list
print("\n--- Processing Metrics ---")
metrics.sort(key=lambda x: x[1])  # Sort by execution time
for rank, (description, execution_time, file_size, word_count) in enumerate(metrics, start=1):
    print(f"{rank}. {description}: {execution_time:.2f} seconds, {file_size:.2f} KB, {word_count} words")

print("\n--- All tests completed ---")
