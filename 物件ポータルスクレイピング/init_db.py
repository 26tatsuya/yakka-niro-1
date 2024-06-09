import sqlite3

def initialize_db(db_path='property.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # テーブル作成の例（適宜修正してください）
    c.execute('''
    CREATE TABLE IF NOT EXISTS SUUMOHOMES (
        id INTEGER PRIMARY KEY,
        名称 TEXT,
        アドレス TEXT,
        家賃 REAL,
        物件詳細URL TEXT,
        緯度 REAL,
        経度 REAL,
        間取り TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS LAVA (
        id INTEGER PRIMARY KEY,
        店舗名 TEXT,
        住所 TEXT,
        リンク TEXT,
        緯度 REAL,
        経度 REAL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS anytime (
        id INTEGER PRIMARY KEY,
        店舗名 TEXT,
        住所 TEXT,
        リンク TEXT,
        緯度 REAL,
        経度 REAL
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()
