import os
import sqlite3

# Check possible sqlite paths
paths = [
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "placement.db"),
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "placement.db")
]

for p in paths:
    if os.path.exists(p):
        print(f"Checking SQLite DB at: {p}")
        conn = sqlite3.connect(p)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE application ADD COLUMN application_summary VARCHAR(300);")
            conn.commit()
            print(f"  ✔ Added application_summary column to SQLite table 'application' in {p}")
        except Exception as e:
            print(f"  Note on ALTER TABLE in {p}: {e}")
        conn.close()
print("✔ SQLite schema check complete!")
