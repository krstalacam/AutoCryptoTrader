from db_manager import DBManager


def create_tables():
    """
    Veritabanı tablolarını oluşturur.
    """
    db = DBManager()

    # High Priority Tablosu
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS high_priority (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE,
        avg_profit_rate REAL NOT NULL,
        lock_time INTEGER DEFAULT 20
    )
    """)

    # Low Priority Tablosu
    db.execute_query("""
    CREATE TABLE IF NOT EXISTS low_priority (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE,
        volume INTEGER NOT NULL,
        ma25_angle REAL NOT NULL
    )
    """)

    db.close()
    print("Tablolar başarıyla oluşturuldu!")


if __name__ == "__main__":
    create_tables()
