import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
import os


# Function to extract keywords
def extract_keywords(text, top_n=5):
    if pd.isna(text) or text.strip() == "":  # Handle empty or whitespace-only cells
        return ""
    vectorizer = CountVectorizer(max_features=top_n, stop_words="english")
    try:
        keywords = vectorizer.fit_transform([text]).toarray()
        return ", ".join(vectorizer.get_feature_names_out())
    except ValueError:
        return ""  # Handle cases where all words are stop words or text is invalid


# Main function to process the CSV
def process_csv(input_csv, column_to_process, output_column, output_directory):
    try:
        # Load the CSV file
        df = pd.read_csv(input_csv, encoding='utf-8', delimiter=',')

        # Preprocess the column: Remove NaN, strip whitespace
        df = df[df[column_to_process].notna()]  # Remove rows where the column is NaN
        df[column_to_process] = df[column_to_process].str.strip()  # Strip whitespace

        # Extract keywords from the specified column
        df[output_column] = df[column_to_process].apply(extract_keywords)

        # Generate output file name
        base_name = os.path.basename(input_csv)  # Get the input file name
        base_name_without_ext = os.path.splitext(base_name)[0]
        output_csv = os.path.join(output_directory, f"{base_name_without_ext}_keyworded.csv")

        # Save the updated data to the output directory
        os.makedirs(output_directory, exist_ok=True)  # Ensure the directory exists
        df.to_csv(output_csv, index=False)
        print(f"Keywords extracted and saved to '{output_csv}'.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage
if __name__ == "__main__":
    # Paths and column names
    input_csv_path = r"C:\Users\cicai\PycharmProjects\MemryB\Sandbox\Experimental\X86\Junkyard\copilot-activity-history.csv"  # Path to your input CSV file
    column_to_process = "Message"  # Name of the column containing text
    output_column = "Keywords"  # Name of the new column for keywords
    output_directory = r"C:\Users\cicai\PycharmProjects\MemryB\Sandbox\Experimental\X86\Output\Spreadsheet"

    process_csv(input_csv_path, column_to_process, output_column, output_directory)
