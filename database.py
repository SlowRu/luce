# database.py
import sqlite3
from datetime import datetime
from typing import Optional
import json

class Database:
    def __init__(self, db_path: str = "game_bot.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    stars_balance INTEGER DEFAULT 0,
                    ton_balance REAL DEFAULT 0.0,
                    total_games INTEGER DEFAULT 0,
                    total_wins INTEGER DEFAULT 0,
                    total_wagered_stars INTEGER DEFAULT 0,
                    total_wagered_ton REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица транзакций
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    currency TEXT,
                    amount REAL,
                    status TEXT,
                    telegram_payment_id TEXT,
                    ton_tx_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица истории игр
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    game_type TEXT,
                    bet_amount REAL,
                    currency TEXT,
                    result TEXT,
                    win_amount REAL,
                    game_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            conn.commit()
    
    def get_user(self, user_id: int) -> Optional[dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
    
    def create_user(self, user_id: int, username: str = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
                (user_id, username)
            )
            conn.commit()
    
    def update_balance(self, user_id: int, currency: str, amount: float):
        field = 'stars_balance' if currency == 'stars' else 'ton_balance'
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'UPDATE users SET {field} = {field} + ? WHERE user_id = ?',
                (amount, user_id)
            )
            conn.commit()
    
    def get_balance(self, user_id: int, currency: str) -> float:
        user = self.get_user(user_id)
        if not user:
            return 0
        return user['stars_balance'] if currency == 'stars' else user['ton_balance']
    
    def add_transaction(self, user_id: int, tx_type: str, currency: str, 
                       amount: float, status: str, **kwargs):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, type, currency, amount, status, telegram_payment_id, ton_tx_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, tx_type, currency, amount, status,
                  kwargs.get('telegram_payment_id'),
                  kwargs.get('ton_tx_hash')))
            conn.commit()
    
    def add_game_record(self, user_id: int, game_type: str, bet_amount: float,
                       currency: str, result: str, win_amount: float, game_data: dict):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO game_history 
                (user_id, game_type, bet_amount, currency, result, win_amount, game_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, game_type, bet_amount, currency, result, 
                  win_amount, json.dumps(game_data)))
            
            # Обновляем статистику
            cursor.execute('''
                UPDATE users SET 
                    total_games = total_games + 1,
                    total_wins = total_wins + ?,
                    total_wagered_stars = total_wagered_stars + ?,
                    total_wagered_ton = total_wagered_ton + ?
                WHERE user_id = ?
            ''', (1 if result == 'win' else 0,
                  bet_amount if currency == 'stars' else 0,
                  bet_amount if currency == 'ton' else 0,
                  user_id))
            conn.commit()

db = Database()