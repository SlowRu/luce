# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery,
    CallbackQuery, Message
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database import db
from games import CoinFlip, Dice, HighLow, Slots, Mines, GameResult
from payments import star_payments, ton_payments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Новый способ инициализации в aiogram 3.13
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# ── FSM States ──────────────────────────────────────────────
class GameStates(StatesGroup):
    choosing_game    = State()
    choosing_currency = State()
    entering_bet     = State()
    playing_coinflip = State()
    playing_dice     = State()
    playing_highlow  = State()
    playing_slots    = State()
    playing_mines    = State()


class DepositStates(StatesGroup):
    choosing_currency = State()
    entering_amount   = State()
    waiting_payment   = State()


# ── Keyboards ───────────────────────────────────────────────
def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть",      callback_data="play")],
        [InlineKeyboardButton(text="💰 Депозит",     callback_data="deposit"),
         InlineKeyboardButton(text="💸 Вывод",       callback_data="withdraw")],
        [InlineKeyboardButton(text="👛 Баланс",      callback_data="balance"),
         InlineKeyboardButton(text="📊 Статистика",  callback_data="stats")],
    ])

def games_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Монетка",  callback_data="game_coinflip"),
         InlineKeyboardButton(text="🎲 Кости",    callback_data="game_dice")],
        [InlineKeyboardButton(text="📈 High/Low", callback_data="game_highlow"),
         InlineKeyboardButton(text="🎰 Слоты",    callback_data="game_slots")],
        [InlineKeyboardButton(text="💣 Мины",     callback_data="game_mines")],
        [InlineKeyboardButton(text="◀️ Назад",    callback_data="back_main")],
    ])

def currency_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Stars", callback_data="currency_stars"),
         InlineKeyboardButton(text="💎 TON",   callback_data="currency_ton")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_games")],
    ])

def coinflip_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌕 Орёл",   callback_data="flip_heads"),
         InlineKeyboardButton(text="🌑 Решка",  callback_data="flip_tails")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_game")],
    ])

def dice_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"dice_{i}") for i in range(1, 4)],
        [InlineKeyboardButton(text=str(i), callback_data=f"dice_{i}") for i in range(4, 7)],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_game")],
    ])

def highlow_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Выше 50", callback_data="hl_high"),
         InlineKeyboardButton(text="📉 Ниже 50", callback_data="hl_low")],
        [InlineKeyboardButton(text="◀️ Отмена",  callback_data="cancel_game")],
    ])

def slots_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Крутить!", callback_data="spin_slots")],
        [InlineKeyboardButton(text="◀️ Назад",   callback_data="back_games")],
    ])

def mines_keyboard(game_state: dict):
    revealed = set(game_state["revealed"])
    mines    = set(game_state["mines"]) if game_state["game_over"] else set()

    keyboard = []
    for row in range(5):
        row_buttons = []
        for col in range(5):
            cell = row * 5 + col
            if cell in revealed:
                text = "💎"
            elif cell in mines:
                text = "💥"
            else:
                text = "⬜"
            row_buttons.append(
                InlineKeyboardButton(text=text, callback_data=f"mine_{cell}")
            )
        keyboard.append(row_buttons)

    keyboard.append([
        InlineKeyboardButton(
            text=f"💰 Забрать (x{game_state['multiplier']})",
            callback_data="mines_cashout"
        ),
        InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_game"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def play_again_keyboard(game: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Играть снова", callback_data=f"game_{game}")],
        [InlineKeyboardButton(text="◀️ В меню",       callback_data="back_main")],
    ])


# ── Helpers ─────────────────────────────────────────────────
def currency_symbol(currency: str) -> str:
    return "⭐" if currency == "stars" else "💎"


# ── /start ───────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message):
    db.create_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "🎰 *Добро пожаловать в Game Bot!*\n\n"
        "Здесь вы можете играть в азартные игры на:\n"
        "⭐ Telegram Stars\n"
        "💎 TON\n\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard()
    )


# ── Баланс / Статистика ──────────────────────────────────────
@dp.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    db.create_user(callback.from_user.id)
    user = db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"👛 *Ваш баланс:*\n\n"
        f"⭐ Stars: *{user['stars_balance']}*\n"
        f"💎 TON: *{user['ton_balance']:.2f}*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
        ])
    )

@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Статистика недоступна")
        return
    win_rate = (
        user["total_wins"] / user["total_games"] * 100
        if user["total_games"] > 0 else 0
    )
    await callback.message.edit_text(
        f"📊 *Ваша статистика:*\n\n"
        f"🎮 Всего игр: *{user['total_games']}*\n"
        f"🏆 Побед: *{user['total_wins']}*\n"
        f"📈 Винрейт: *{win_rate:.1f}%*\n\n"
        f"⭐ Поставлено Stars: *{user['total_wagered_stars']}*\n"
        f"💎 Поставлено TON: *{user['total_wagered_ton']:.2f}*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", 
