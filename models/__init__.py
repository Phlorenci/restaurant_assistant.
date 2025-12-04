# models package
import sqlite3

conn = sqlite3.connect("test.db")
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS demo (id INTEGER PRIMARY KEY, name TEXT)")
cursor.execute("INSERT INTO demo (name) VALUES (?)", ("Hello",))
conn.commit()

cursor.execute("SELECT * FROM demo")
print(cursor.fetchall())

conn.close()