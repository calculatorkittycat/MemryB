from openai import OpenAI
from Config.config import openai_api_key

# OpenAI API Configuration
openai_api_key = openai_api_key
client = OpenAI(api_key=openai_api_key)

def chat_with_llm(prompt):
    """
    Sends a text prompt to the OpenAI API and retrieves the response.

    Args:
        prompt (str): The user input to send to the LLM.

    Returns:
        str: The LLM's response to the prompt.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Replace with your desired OpenAI model ID
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    print("Welcome to the LLM Chat Console!")
    print("Type 'exit' to quit the chat.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        try:
            llm_response = chat_with_llm(user_input)
            print(f"LLM: {llm_response}\n")
        except Exception as e:
            print(f"An error occurred: {e}")
