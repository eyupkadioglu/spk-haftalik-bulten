import sqlite3, os
# Flask SQLAlchemy uses instance folder for sqlite:///
for db_path in ["instance/eticaret.db", "eticaret.db", "app.db"]:
    if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
        print(f"Using: {db_path} ({os.path.getsize(db_path)} bytes)")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        print("Tables:", tables)
        for tbl in ["teklifler", "stok"]:
            cur.execute(f"PRAGMA table_info({tbl})")
            cols = cur.fetchall()
            print(f"\n{tbl}: {[c[1] for c in cols]}")
        conn.close()
        break
else:
    print("No non-empty DB found")
