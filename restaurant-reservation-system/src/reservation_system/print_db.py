# print_db.py
import sqlite3, json

DB = 'reservation.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for t in tables:
    print(f"\n--- TABLE: {t} ---")
    try:
        cur.execute(f"SELECT * FROM {t} LIMIT 100")
        cols = [d[0] for d in cur.description]
        for row in cur.fetchall():
            print(dict(zip(cols, row)))
    except Exception as e:
        print('  (error reading table)', e)

conn.close()