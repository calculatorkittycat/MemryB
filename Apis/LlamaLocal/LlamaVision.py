import subprocess

def chat_with_llama(prompt):
    """
    Sends a prompt to the llama3.2 model via the ollama CLI and returns the response.
    """
    ollama_path = r"C:\Users\cicai\AppData\Local\Programs\Ollama\ollama.exe"  # Full path to Ollama executable

    try:
        # Run the Ollama command and pass the prompt
        process = subprocess.Popen(
            [ollama_path, 'run', 'llama3.2-vision'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Send the prompt to the model and get the response
        stdout, stderr = process.communicate(input=prompt)

       # if stderr:
            #print(f"Error: {stderr}")
        return stdout.strip()

    except FileNotFoundError:
        return "Error: The 'ollama' CLI is not found. Ensure the path is correct."

# Chat loop
if __name__ == "__main__":
    print("Chat with llama3.2 (type 'exit' to quit):")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = chat_with_llama(user_input)
        print(f"llama3.2: {response}")
