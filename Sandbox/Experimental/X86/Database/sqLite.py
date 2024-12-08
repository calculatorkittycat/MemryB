import sqlite3

####This Script creates a new example table####
connection = sqlite3.connect("example.db")
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
cursor.execute("INSERT INTO test (name) VALUES ('SQLite Installed')")
connection.commit()
connection.close()
print("SQLite setup successful!")
