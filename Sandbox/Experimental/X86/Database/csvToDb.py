import sqlite3
import csv
import os
######Define paths within main at end of script######


def csv_to_db(csv_file, db_file, table_name):
    try:
        # Connect to SQLite database (creates the .db file if it doesn't exist)
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()

        # Read the CSV file
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)  # Extract header row

            # Create table with columns based on CSV headers
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {', '.join([f'"{header}" TEXT' for header in headers])}
                )
            """)

            # Insert rows from the CSV file into the table
            for row in reader:
                cursor.execute(f"""
                    INSERT INTO {table_name} ({', '.join([f'"{header}"' for header in headers])})
                    VALUES ({', '.join(['?' for _ in headers])})
                """, row)

        # Commit changes and close the connection
        connection.commit()
        print(f"Successfully converted '{csv_file}' to '{db_file}' with table '{table_name}'.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()


# Example usage
if __name__ == "__main__":
    # Input CSV file and output database
    csv_file_path = r"C:\Users\cicai\PycharmProjects\MemryB\Sandbox\Experimental\X86\Output\Spreadsheet\copilot-activity-history_keyworded.csv" # Path to your CSV file
    db_file_path = "Copilot_Activity_Keyworded.db"  # Name of the output .db file
    table_name = "Activity_History"  # Table name in the database

    if os.path.exists(csv_file_path):
        csv_to_db(csv_file_path, db_file_path, table_name)
    else:
        print(f"Error: The file '{csv_file_path}' does not exist.")
