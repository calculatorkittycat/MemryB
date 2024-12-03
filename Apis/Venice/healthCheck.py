import json
import requests
from Config.config import VENICE_API_KEY, VENICE_API_CHAT_ENDPOINT, MODEL_ID, API_TIMEOUT, TEST_PROMT

class VeniceAPIHealthChecker:

    def check_health(self):

        print(f"Performing API health check using: {MODEL_ID}, With Api timeout of {API_TIMEOUT}")
        headers = {
            "Authorization": f"Bearer {VENICE_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": TEST_PROMT}]
        }
        try:
            response = requests.post(
                f"{VENICE_API_CHAT_ENDPOINT}/chat/completions",
                headers=headers,
                json=data,
                timeout=API_TIMEOUT
            )
            if response.status_code == 200:
                print(f"API health check successful. \nPrompt Sent: {TEST_PROMT}\nResponse: {response.json()['choices'][0]['message']['content']}")
                #UNCOMMENT BELOW TO SEE FULL API RESPONSE
                ##print("\nFull Response Below \n \n")
                ##print(json.dumps(response.json(), indent=4))

            else:
                print(f"API health check failed with status code {response.status_code}: {response.text}")
                raise RuntimeError("API health check failed.")
        except requests.exceptions.RequestException as e:
            print(f"API health check failed with error: {e}")
            raise RuntimeError("API health check failed.")

def main():
    """
    Main function to execute the health check.
    """
    health_checker = VeniceAPIHealthChecker()
    health_checker.check_health()

if __name__ == "__main__":
    main()
