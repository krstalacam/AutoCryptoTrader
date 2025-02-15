import sqlite3


class DBManager:
    def __init__(self):
        self.connection = sqlite3.connect('database.db')
        self.cursor = self.connection.cursor()
        self.create_tables()  # Tabloları oluştur

    def create_tables(self):
        # low_priority tablosunu oluştur
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS low_priority (
            symbol TEXT PRIMARY KEY,
            volume INTEGER,
            ma25_angle INTEGER
        )
        """)

        # high_priority tablosunu oluştur
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS high_priority (
            symbol TEXT PRIMARY KEY,
            avg_profit_rate REAL,
            lock_time INTEGER
        )
        """)

        # Değişiklikleri kaydet
        self.connection.commit()

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
