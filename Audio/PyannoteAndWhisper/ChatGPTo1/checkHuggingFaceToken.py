import requests

def check_hf_model_access(model_id: str, hf_token: str):
    """
    Checks if the provided HF token can access the specified Hugging Face model.

    :param model_id: The model's repo ID, e.g. "pyannote/speaker-diarization"
    :param hf_token: Your personal Hugging Face access token
    :return: True if accessible, False otherwise
    """
    url = f"https://huggingface.co/api/models/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"[INFO] Successfully accessed '{model_id}'.")
            return True
        else:
            print(f"[ERROR] Could not access '{model_id}'.")
            print(f"       HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to check access for '{model_id}': {e}")
        return False

if __name__ == "__main__":
    # Replace with your own model and token
    MODEL_ID = "pyannote/speaker-diarization"
    HF_TOKEN = "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"

    has_access = check_hf_model_access(MODEL_ID, HF_TOKEN)
    print(f"[RESULT] Access check = {has_access}")
