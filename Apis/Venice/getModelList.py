import requests
import json
from Config.config import VENICE_API_KEY, VENICE_API_GET_MODEL_LIST_ENDPOINT

# Set up headers
headers = {"Authorization": f"Bearer {VENICE_API_KEY}"}

# Make the GET request
response = requests.request("GET", VENICE_API_GET_MODEL_LIST_ENDPOINT, headers=headers)

# Process the response JSON
response_json = response.json()

#Print Entire Pretty Response
#print(json.dumps(response.json(), indent=4))

# Extract and print desired parts of the JSON response
if "data" in response_json:
    for model in response_json["data"]:
        model_id = model.get("id", "N/A")
        model_type = model.get("type", "N/A")
        context_tokens = model.get("model_spec", {}).get("availableContextTokens", "N/A")
        print(f"\nId: {model_id},\nType: {model_type},\nAvailable Context Tokens: {context_tokens}")
else:
    print("No models found in response.")



