import ollama
import json
import time

# Measure script execution time
start_time = time.time()

# Querying the model
response = ollama.chat(
    model='llama3.2-vision',
    messages=[{
        'role': 'user',
        'content': 'What is in this image?',
        'images': ['XnRmqt5.jpg']
    }]
)

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

# Call the pretty print function
pretty_print_response(response)

# Print script execution time
end_time = time.time()
execution_time = end_time - start_time
print(f"\n--- Script Execution Time: {execution_time:.2f} seconds ---")
