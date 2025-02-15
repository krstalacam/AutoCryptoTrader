class CryptoOperations:
    def __init__(self, db):
        self.db = db

    def add_to_low_priority(self, volume, ma25_angle, symbol):
        query = """
        INSERT INTO low_priority (symbol, volume, ma25_angle)
        VALUES (?, ?, ?)
        """
        self.db.execute_query(query, (symbol, volume, ma25_angle))

    def add_to_high_priority(self, avg_profit_rate, symbol):
        query = """
        INSERT INTO high_priority (symbol, avg_profit_rate)
        VALUES (?, ?)
        """
        self.db.execute_query(query, (symbol, avg_profit_rate))

    def fetch_all_low_priority(self):
        return self.db.fetch_all("""
        SELECT symbol, volume, ma25_angle
        FROM low_priority
        """)

    def fetch_all_high_priority(self):
        return self.db.fetch_all("""
        SELECT symbol, avg_profit_rate, lock_time
        FROM high_priority
        """)

    def fetch_one_low_priority(self):
        return self.db.fetch_one("""
        SELECT symbol, volume, ma25_angle
        FROM low_priority
        ORDER BY ma25_angle DESC, volume DESC
        LIMIT 1
        """)

    def fetch_one_high_priority(self):
        return self.db.fetch_one("""
        SELECT symbol, avg_profit_rate, lock_time
        FROM high_priority
        ORDER BY avg_profit_rate DESC
        LIMIT 1
        """)

    def execute_query(self, query, params=()):
        self.db.execute_query(query, params)
