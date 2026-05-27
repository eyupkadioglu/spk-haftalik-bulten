import sqlite3

conn = sqlite3.connect("instance/eticaret.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS firma_ayar (
    id INTEGER PRIMARY KEY,
    firma_adi VARCHAR(200) DEFAULT '',
    adres TEXT DEFAULT '',
    telefon VARCHAR(50) DEFAULT '',
    email VARCHAR(120) DEFAULT '',
    website VARCHAR(120) DEFAULT '',
    vergi_no VARCHAR(20) DEFAULT '',
    vergi_dairesi VARCHAR(100) DEFAULT '',
    logo VARCHAR(255),
    varsayilan_para_birimi VARCHAR(5) DEFAULT 'TRY',
    teklif_notu TEXT DEFAULT '',
    fatura_notu TEXT DEFAULT ''
)
""")
print("firma_ayar table created/verified")

conn.commit()
conn.close()
print("Done.")
