from ollama._client import Client

def main():
    # Initialize the Ollama client
    client = Client()

    # Specify the model (Phi4 in this case)
    model_name = "Phi4"

    print(f"Chatting with model: {model_name}")
    print("Type 'exit' to end the chat.\n")

    # Start an interactive chat loop
    while True:
        # Get user input
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Chat ended.")
            break

        try:
            # Send the input to the model and get the response
            response = client.chat(model=model_name, messages=[{"role": "user", "content": user_input}])
            # Print the assistant's response
            print(f"Phi4: {response.message.content}")
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()
