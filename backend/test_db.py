import mysql.connector

try:
    conn = mysql.connector.connect(
        host="mysql-production-99fb.up.railway.app",
        port=5432,
        user="root",
        password="SEOHmFhVsufbiwxOOGDUyyWUegNxzqPJ",
        database="railway",
        ssl_disabled=False,
        ssl_verify_cert=False,
        ssl_verify_identity=False,
        connection_timeout=15,
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print(f"✓ Bağlantı başarılı: {cursor.fetchone()}")
    conn.close()
except Exception as e:
    print(f"✗ Başarısız: {e}")
