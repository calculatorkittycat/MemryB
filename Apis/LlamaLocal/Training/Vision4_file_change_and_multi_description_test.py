import ollama
import json
import time
import os
from PIL import Image

# Image file path
image_path = 'XnRmqt5.jpg'

# Prompts to test
prompts = [
    "What is in this image?",
    "Briefly describe the content of this image.",
    "What key elements are visible in this photo?",
    "Summarize the main details in this image.",
    "Provide a short description of the image.",
    "List the important objects in this picture."
]

# To store all results
all_results = []

# Function to process the image with the model
def process_image(image, description, prompt):
    start_time = time.time()
    temp_image_path = 'temp_image.jpg'
    image.save(temp_image_path)
    file_size = os.path.getsize(temp_image_path) / 1024  # Convert to KB
    response = ollama.chat(
        model='llama3.2-vision',
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [temp_image_path]
        }]
    )
    end_time = time.time()
    execution_time = end_time - start_time

    # Calculate word count of the message content
    word_count = len(response.message.content.split())

    # Store metrics and response
    all_results.append({
        "description": description,
        "prompt": prompt,
        "execution_time": execution_time,
        "file_size": file_size,
        "word_count": word_count,
        "response": response.message.content
    })

# Load the original image
original_image = Image.open(image_path)

# Process for each prompt
def process_with_all_prompts():
    for prompt in prompts:
        # 1. Process the original image (normal)
        process_image(original_image, "Original Image", prompt)

        # 2. Process the image in black and white
        grayscale_image = original_image.convert('L')
        process_image(grayscale_image, "Black and White Image", prompt)

        # 3. Process the image at 50% resolution
        half_res_image = original_image.resize(
            (original_image.width // 2, original_image.height // 2), Image.Resampling.LANCZOS
        )
        process_image(half_res_image, "Half Resolution Image", prompt)

        # 4. Process the image at 50% resolution in black and white
        half_res_grayscale_image = grayscale_image.resize(
            (grayscale_image.width // 2, grayscale_image.height // 2), Image.Resampling.LANCZOS
        )
        process_image(half_res_grayscale_image, "Half Resolution Black and White Image", prompt)

        # 5. Optional: Experiment with high JPEG compression
        compressed_image_path = 'compressed_image.jpg'
        original_image.save(compressed_image_path, 'JPEG', quality=10)
        compressed_image = Image.open(compressed_image_path)
        process_image(compressed_image, "Highly Compressed Image", prompt)

process_with_all_prompts()

# Save all results to a text file
output_file = "image_processing_results.txt"
with open(output_file, "w") as f:
    for result in all_results:
        f.write(f"Prompt: {result['prompt']}\n")
        f.write(f"Image Description: {result['description']}\n")
        f.write(f"Execution Time: {result['execution_time']:.2f} seconds\n")
        f.write(f"File Size: {result['file_size']:.2f} KB\n")
        f.write(f"Description Word Count: {result['word_count']}\n")
        f.write("Response:\n")
        f.write(result['response'] + "\n\n")

print(f"\n--- All tests completed. Results saved to {output_file} ---")
