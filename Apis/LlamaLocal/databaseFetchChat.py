import subprocess
import sqlite3
from datetime import datetime, timedelta

# Database file path
DB_PATH = r"C:\Users\cicai\PycharmProjects\MemryB\Sandbox\Experimental\X86\Database\Copilot_Activity_Keyworded.db"

# Global variable to store the latest query results
latest_query_results = None

def execute_query(query):
    """
    Executes an SQL query on the database and returns the results.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except sqlite3.Error as e:
        return f"Database error: {e}"

def chat_with_llama(prompt):
    """
    Sends a prompt to the llama3.2 model via the Ollama CLI and returns the response.
    """
    ollama_path = r"C:\Users\cicai\AppData\Local\Programs\Ollama\ollama.exe"  # Full path to Ollama executable

    try:
        # Run the Ollama command and pass the prompt
        process = subprocess.Popen(
            [ollama_path, 'run', 'llama3.2'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Send the prompt to the model and get the response
        stdout, stderr = process.communicate(input=prompt)
        return stdout.strip()
    except FileNotFoundError:
        return "Error: The 'ollama' CLI is not found. Ensure the path is correct."

def generate_week_dates(year, month, week_start):
    """
    Generates date strings for the first week of a given month.
    """
    base_date = datetime(year, month, week_start)
    return [(base_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

if __name__ == "__main__":
    # Get today's date
    today_date = datetime.now().strftime("%Y-%m-%d")

    # Context about the table structure with today's date
    TABLE_CONTEXT = f"""
    The table 'Activity_History' contains the following structure:
    1. 'Conversation' (TEXT): Refers to the conversation or session name.
    2. 'Time' (TEXT): Contains the timestamps of each message in the format 'YYYY-MM-DDTHH:MM:SS'.
    3. 'Author' (TEXT): Indicates the speaker. Values can be 'Ai' (for Copilot) or 'Human' (for you).
    4. 'Message' (TEXT): Contains the content of the message.
    5. 'Keywords' (TEXT): Contains keywords extracted from the 'Message' column.

    This table logs a conversation history. Questions about specific dates, months, messages, authors, or keywords will result in SQL queries being generated and executed to retrieve relevant information.
    Ensure queries for specific days or months match timestamps flexibly using the LIKE operator with a wildcard ('%').

    Today's date is {today_date}.
    """

    print("The language model is aware of the following table structure:")
    print(TABLE_CONTEXT)
    print("\nYou can now ask questions about the table. Type 'exit' to quit.")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break

        # Handle "Query:" prompts
        if user_input.startswith("Query:"):
            query_text = user_input[len("Query:"):].strip()

            # Pass the user query and table context to the language model
            prompt = (
                f"{TABLE_CONTEXT}\n\nUser Query: {query_text}\n\n"
                "Generate an SQL query based on the above table structure to retrieve the requested information. "
                "Include only the query itself in the response, and ensure it is valid SQL."
            )
            sql_query = chat_with_llama(prompt)

            print(f"\nGenerated SQL Query:\n{sql_query}")

            # Execute the generated query and fetch results
            query_results = execute_query(sql_query)
            latest_query_results = query_results  # Store results for follow-up questions

            if isinstance(query_results, str):  # Error message
                print(f"\nError executing query: {query_results}")
            else:
                # Format the results for readability
                formatted_results = (
                    "Query Results:\n" + "\n".join(str(row) for row in query_results)
                    if query_results
                    else "No results found."
                )
                print(f"\n{formatted_results}")

        # Handle conversational prompts
        else:
            if latest_query_results:
                # Include the latest query results in the conversation context
                prompt = (
                    f"Here are the latest query results:\n{latest_query_results}\n\n"
                    f"User's question: {user_input}\n\n"
                    "Provide a helpful response based on the query results above."
                )
            else:
                # No query results yet, handle as a regular prompt
                prompt = user_input

            response = chat_with_llama(prompt)
            print(f"llama3.2: {response}")
