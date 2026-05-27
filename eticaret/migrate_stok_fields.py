import sqlite3

conn = sqlite3.connect("instance/eticaret.db")
cur = conn.cursor()

cols = [row[1] for row in cur.execute("PRAGMA table_info(stok)").fetchall()]
print("Mevcut kolonlar:", cols)

new_cols = [
    ("urun_tipi",        "VARCHAR(10) DEFAULT 'stok'"),
    ("marka",            "VARCHAR(100)"),
    ("tedarikci_id",     "INTEGER REFERENCES cari(id)"),
    ("tedarikci_kodu",   "VARCHAR(100)"),
    ("alis_kdv_orani",   "NUMERIC(5,2) DEFAULT 20"),
    ("alis_para_birimi", "VARCHAR(5) DEFAULT 'TRY'"),
    ("satis_para_birimi","VARCHAR(5) DEFAULT 'TRY'"),
]

for col, typ in new_cols:
    if col not in cols:
        cur.execute(f"ALTER TABLE stok ADD COLUMN {col} {typ}")
        print(f"  + {col}")
    else:
        print(f"  = {col} (zaten var)")

conn.commit()
conn.close()
print("Done.")
