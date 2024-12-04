import base64
from openai import OpenAI
from Config.config import openai_api_key

# OpenAI API Configuration
openai_api_key = openai_api_key
client = OpenAI(api_key=openai_api_key)


def encode_image(image_path):
    """
    Encodes an image file to Base64 format.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Base64 encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_image_summary(image_path):
    """
    Fetches a summary of the content in the provided image using OpenAI API.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Summary of the image content.
    """
    base64_image = encode_image(image_path)
    data_url = f"data:image/png;base64,{base64_image}"  # Adjust MIME type if necessary

    # Call OpenAI API for the current image
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Replace with your OpenAI model ID if needed
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url,
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    # Extract content summary from the response
    content_summary = response.choices[0].message.content
    return content_summary

# Place the following at the bottom of your script:

if __name__ == "__main__":
    image_path = "../Input/Images/testImage.jpg"
    try:
        summary = get_image_summary(image_path)
        print(f"Image Summary: {summary}")
    except Exception as e:
        print(f"An error occurred: {e}")
