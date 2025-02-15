from cripto_bot_v1.binance_bot.olds.sql.db_manager import DBManager


class CryptoRanker:
    MAX_LOW_PRIORITY = 10
    MAX_HIGH_PRIORITY = 4

    def __init__(self, db_manager=None):
        self.db_manager = db_manager or DBManager()
        self.db = self.db_manager.cursor

    def calculate_priority_score(self, volume, ma25_angle):
        """Calculate a priority score based on volume and moving average angle."""
        return ma25_angle / max(volume, 1)

    def add_to_low_priority(self, volume, ma25_angle, symbol):
        """Add or update item in low priority queue."""
        try:
            query = '''
            INSERT OR REPLACE INTO low_priority (symbol, volume, ma25_angle)
            VALUES (?, ?, ?)
            '''
            self.db.execute(query, (symbol, volume, ma25_angle))
            self.db.connection.commit()
        except Exception as e:
            print(f"Error adding to low priority: {e}")

    def add_to_high_priority(self, avg_profit_rate, symbol):
        """Add item to high priority queue."""
        try:
            # Remove if exists first
            self.remove_from_high_priority(symbol)

            query = '''
            INSERT INTO high_priority (symbol, avg_profit_rate, lock_time)
            VALUES (?, ?, ?)
            '''
            self.db.execute(query, (symbol, avg_profit_rate, 3))
            self.db.connection.commit()
        except Exception as e:
            print(f"Error adding to high priority: {e}")

    def remove_from_low_priority(self, symbol):
        """Remove item from low priority queue."""
        query = "DELETE FROM low_priority WHERE symbol = ?"
        self.db.execute(query, (symbol,))
        self.db.connection.commit()

    def remove_from_high_priority(self, symbol):
        """Remove item from high priority queue."""
        query = "DELETE FROM high_priority WHERE symbol = ?"
        self.db.execute(query, (symbol,))
        self.db.connection.commit()

    def periodic_maintenance(self):
        """Perform periodic maintenance: update high priority and manage queues."""
        try:
            # Update lock times
            self.db.execute('''
            UPDATE high_priority 
            SET lock_time = CASE 
                WHEN lock_time > 0 THEN lock_time - 1 
                ELSE lock_time
            END
            ''')
            self.db.connection.commit()
            print("Updated lock times for high priority items.")

            # Remove low-profit items from high priority
            self.remove_low_profit_high_priority_items()

            # Promote the best item from low_priority to high_priority
            while self.count_high_priority() < self.MAX_HIGH_PRIORITY:
                self.fetch_and_promote_best()

        except Exception as e:
            print(f"Error in periodic maintenance: {e}")

    def remove_low_profit_high_priority_items(self):
        """Remove items with low profit rate and lock_time 0."""
        try:
            # Select items where lock_time is 0 and avg_profit_rate is below 0.5
            self.db.execute('''
            SELECT symbol, avg_profit_rate FROM high_priority
            WHERE lock_time = 0 AND avg_profit_rate < 0.5
            ''')
            items_to_remove = self.db.fetchall()

            for symbol, avg_profit_rate in items_to_remove:
                # Remove these items from high priority
                self.remove_from_high_priority(symbol)
                print(f"Removed {symbol} from high priority due to low avg_profit_rate ({avg_profit_rate:.2f})")

            self.db.connection.commit()
        except Exception as e:
            print(f"Error removing low profit high priority items: {e}")

    def count_high_priority(self):
        """Count items in high priority queue."""
        self.db.execute("SELECT COUNT(*) FROM high_priority")
        return self.db.fetchone()[0]

    def print_queues(self):
        """Print current state of both queues."""
        print("\n=== High Priority Queue ===")
        self.db.execute('''
        SELECT symbol, avg_profit_rate, lock_time 
        FROM high_priority 
        ORDER BY avg_profit_rate DESC
        ''')
        high_priority = self.db.fetchall()
        for item in high_priority:
            print(f"Symbol: {item[0]}, Profit Rate: {item[1]:.2f}, Lock Time: {item[2]}")

        print("\n=== Low Priority Queue ===")
        self.db.execute('''
        SELECT symbol, volume, ma25_angle 
        FROM low_priority 
        ORDER BY ma25_angle / volume DESC
        ''')
        low_priority = self.db.fetchall()
        for item in low_priority:
            print(f"Symbol: {item[0]}, Volume: {item[1]}, MA25 Angle: {item[2]}")

    def promote_best_to_high_priority(self):
        """
        Promote the best items from low-priority to high-priority based on calculated scores.
        Ensures that the high-priority queue doesn't exceed its maximum capacity.
        """
        try:
            # Calculate remaining space in high priority queue
            remaining_slots = self.MAX_HIGH_PRIORITY - self.count_high_priority()

            if remaining_slots > 0:
                # Fetch top N items based on ma25_angle / volume, limited by remaining slots
                self.db.execute('''
                SELECT symbol, volume, ma25_angle 
                FROM low_priority 
                ORDER BY ma25_angle / volume DESC 
                LIMIT ?
                ''', (remaining_slots,))
                best_items = self.db.fetchall()

                for symbol, volume, ma25_angle in best_items:
                    avg_profit_rate = self.calculate_priority_score(volume, ma25_angle)

                    # Add to high priority and remove from low priority
                    self.add_to_high_priority(avg_profit_rate, symbol)
                    self.remove_from_low_priority(symbol)
                    print(f"Promoted {symbol} to high priority with profit rate {avg_profit_rate:.2f}")
            else:
                print("High priority queue is full. No promotion performed.")
        except Exception as e:
            print(f"Error promoting best items to high priority: {e}")

    def fetch_and_promote_best(self):
        """
        Fetch all items from the low_priority table, sort by ma25_angle / volume ratio,
        and promote the best one to high_priority.
        """
        try:
            # Fetch all items from the low_priority table
            self.db.execute('''
            SELECT symbol, volume, ma25_angle 
            FROM low_priority
            ''')
            items = self.db.fetchall()

            if not items:
                print("No items in low priority to promote.")
                return

            # Calculate scores and find the best one
            best_item = max(items, key=lambda item: item[2] / item[1])  # ma25_angle / volume
            symbol, volume, ma25_angle = best_item
            avg_profit_rate = self.calculate_priority_score(volume, ma25_angle)

            # Add the best item to high priority and remove it from low priority
            self.add_to_high_priority(avg_profit_rate, symbol)
            self.remove_from_low_priority(symbol)
            print(f"Promoted {symbol} to high priority with profit rate {avg_profit_rate:.2f}")
        except Exception as e:
            print(f"Error in fetch_and_promote_best: {e}")
