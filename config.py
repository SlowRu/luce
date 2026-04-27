# config.py
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str = "8680466852:AAGlGmoqRCFOjJsXxk6s7wNWfWV45ylyu3I"
    
    # TON Connect
    TON_WALLET: str = "YOUR_TON_WALLET_ADDRESS"
    TONCENTER_API_KEY: str = "YOUR_TONCENTER_API_KEY"
    
    # Настройки игр
    MIN_BET_STARS: int = 1
    MAX_BET_STARS: int = 1000
    MIN_BET_TON: float = 0.1
    MAX_BET_TON: float = 100.0
    
    # Комиссия казино (5%)
    HOUSE_EDGE: float = 0.05

config = Config()
