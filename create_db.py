import sqlite3

conn = sqlite3.connect("customers.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT UNIQUE,
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    password TEXT
);
""")

conn.commit()
conn.close()

print("✅ Database Created / Updated")
