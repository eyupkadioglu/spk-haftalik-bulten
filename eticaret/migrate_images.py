import sqlite3

conn = sqlite3.connect("instance/eticaret.db")
cur = conn.cursor()

# Add siparis_id to teklifler
cols = [row[1] for row in cur.execute("PRAGMA table_info(teklifler)").fetchall()]
if "siparis_id" not in cols:
    cur.execute("ALTER TABLE teklifler ADD COLUMN siparis_id INTEGER REFERENCES siparis(id)")
    print("Added siparis_id to teklifler")
else:
    print("siparis_id already exists in teklifler")

# Add resim to stok
cols = [row[1] for row in cur.execute("PRAGMA table_info(stok)").fetchall()]
if "resim" not in cols:
    cur.execute("ALTER TABLE stok ADD COLUMN resim VARCHAR(255)")
    print("Added resim to stok")
else:
    print("resim already exists in stok")

conn.commit()
conn.close()
print("Done.")
