# payments.py
import aiohttp
import hashlib
import time
from config import config

class StarPayments:
    """Обработка платежей через Telegram Stars"""
    
    @staticmethod
    def create_invoice_payload(user_id: int, amount: int, purpose: str) -> str:
        """Создаёт payload для инвойса"""
        return f"{user_id}:{amount}:{purpose}:{int(time.time())}"
    
    @staticmethod
    def parse_invoice_payload(payload: str) -> dict:
        """Парсит payload инвойса"""
        parts = payload.split(':')
        return {
            'user_id': int(parts[0]),
            'amount': int(parts[1]),
            'purpose': parts[2],
            'timestamp': int(parts[3])
        }

class TONPayments:
    """Обработка платежей в TON"""
    
    def __init__(self):
        self.api_url = "https://toncenter.com/api/v2"
        self.api_key = config.TONCENTER_API_KEY
    
    async def get_transactions(self, limit: int = 10) -> list:
        """Получает последние транзакции кошелька"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_url}/getTransactions"
            params = {
                'address': config.TON_WALLET,
                'limit': limit,
                'api_key': self.api_key
            }
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                return data.get('result', [])
    
    async def check_payment(self, expected_amount: float, memo: str) -> bool:
        """Проверяет входящий платёж"""
        transactions = await self.get_transactions()
        
        for tx in transactions:
            if tx.get('in_msg'):
                in_msg = tx['in_msg']
                amount = int(in_msg.get('value', 0)) / 1e9  # нанотоны в TON
                message = in_msg.get('message', '')
                
                if amount >= expected_amount and memo in message:
                    return True
        
        return False
    
    @staticmethod
    def generate_payment_memo(user_id: int) -> str:
        """Генерирует уникальный memo для платежа"""
        data = f"{user_id}:{int(time.time())}"
        return hashlib.md5(data.encode()).hexdigest()[:8]
    
    @staticmethod
    def generate_payment_link(amount: float, memo: str) -> str:
        """Генерирует ссылку для оплаты через Tonkeeper"""
        # Формат: ton://transfer/<address>?amount=<nanotons>&text=<memo>
        nanotons = int(amount * 1e9)
        return f"ton://transfer/{config.TON_WALLET}?amount={nanotons}&text={memo}"

ton_payments = TONPayments()
star_payments = StarPayments()