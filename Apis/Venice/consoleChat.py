import requests
import json
from Config.config import VENICE_API_KEY, VENICE_API_CHAT_ENDPOINT, MODEL_ID, API_TIMEOUT

class VeniceChat:
    """
    A class to interact with the Venice AI system in a console-based chat interface.
    """
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {VENICE_API_KEY}",
            "Content-Type": "application/json"
        }

    def send_message(self, message):
        """
        Send a message to the Venice AI system and return the response.
        """
        data = {
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": message}]
        }
        try:
            response = requests.post(
                f"{VENICE_API_CHAT_ENDPOINT}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=API_TIMEOUT
            )
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                return ai_response
            else:
                print(f"Error: API responded with status code {response.status_code}. Message: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to send message. Exception: {e}")
            return None

def main():
    """
    Main function to handle the console chat interface.
    """
    print("Welcome to the Venice AI Chat Interface!")
    print("Type 'exit' to quit the chat.\n")

    venice_chat = VeniceChat()

    while True:
        user_message = input("You: ")
        if user_message.lower() == "exit":
            print("Exiting chat. Goodbye!")
            break

        response = venice_chat.send_message(user_message)
        if response:
            print(f"Venice AI: {response}")
        else:
            print("Venice AI: Sorry, there was an issue processing your request.")

if __name__ == "__main__":
    main()
