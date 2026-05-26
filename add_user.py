import sqlite3

conn = sqlite3.connect('finance.db')

conn.execute(
    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
    ("Riya", "admin", "123")
)

conn.commit()
conn.close()

print("User added !!")