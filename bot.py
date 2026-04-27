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
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
        ])
    )


# ── Выбор игры ───────────────────────────────────────────────
@dp.callback_query(F.data == "play")
async def choose_game(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GameStates.choosing_game)
    await callback.message.edit_text(
        "🎮 *Выберите игру:*\n\n"
        "🪙 *Монетка* — угадай сторону (x1.9)\n"
        "🎲 *Кости* — угадай число (x5.7)\n"
        "📈 *High/Low* — выше или ниже 50 (x1.9)\n"
        "🎰 *Слоты* — классические слоты (до x50)\n"
        "💣 *Мины* — открывай безопасные ячейки",
        reply_markup=games_keyboard()
    )

@dp.callback_query(F.data.startswith("game_"))
async def select_game(callback: CallbackQuery, state: FSMContext):
    game = callback.data.replace("game_", "")
    await state.update_data(selected_game=game)
    await state.set_state(GameStates.choosing_currency)
    await callback.message.edit_text(
        "💰 *Выберите валюту для ставки:*",
        reply_markup=currency_keyboard()
    )

@dp.callback_query(F.data.startswith("currency_"))
async def select_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.replace("currency_", "")
    await state.update_data(currency=currency)
    await state.set_state(GameStates.entering_bet)

    user_id  = callback.from_user.id
    balance  = db.get_balance(user_id, currency)
    sym      = currency_symbol(currency)
    min_bet  = config.MIN_BET_STARS  if currency == "stars" else config.MIN_BET_TON
    max_bet  = config.MAX_BET_STARS  if currency == "stars" else config.MAX_BET_TON

    await callback.message.edit_text(
        f"💰 *Введите сумму ставки*\n\n"
        f"Ваш баланс: {sym} *{balance}*\n"
        f"Мин. ставка: {min_bet}\n"
        f"Макс. ставка: {max_bet}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_game")]
        ])
    )


# ── Ввод ставки ──────────────────────────────────────────────
@dp.message(GameStates.entering_bet)
async def process_bet(message: Message, state: FSMContext):
    try:
        bet = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите корректное число")
        return

    data     = await state.get_data()
    currency = data["currency"]
    game     = data["selected_game"]
    user_id  = message.from_user.id
    sym      = currency_symbol(currency)

    min_bet  = config.MIN_BET_STARS if currency == "stars" else config.MIN_BET_TON
    max_bet  = config.MAX_BET_STARS if currency == "stars" else config.MAX_BET_TON
    balance  = db.get_balance(user_id, currency)

    if bet < min_bet:
        await message.answer(f"❌ Минимальная ставка: {min_bet}")
        return
    if bet > max_bet:
        await message.answer(f"❌ Максимальная ставка: {max_bet}")
        return
    if bet > balance:
        await message.answer(f"❌ Недостаточно средств. Баланс: {balance}")
        return

    await state.update_data(bet=bet)

    if game == "coinflip":
        await state.set_state(GameStates.playing_coinflip)
        await message.answer(
            f"🪙 *Монетка*\n\nСтавка: *{bet}* {sym}\nВыигрыш: *x1.9*\n\nВыберите сторону:",
            reply_markup=coinflip_keyboard()
        )
    elif game == "dice":
        await state.set_state(GameStates.playing_dice)
        await message.answer(
            f"🎲 *Кости*\n\nСтавка: *{bet}* {sym}\nВыигрыш: *x5.7*\n\nВыберите число от 1 до 6:",
            reply_markup=dice_keyboard()
        )
    elif game == "highlow":
        await state.set_state(GameStates.playing_highlow)
        await message.answer(
            f"📈 *High/Low*\n\nСтавка: *{bet}* {sym}\nВыигрыш: *x1.9*\n\nБудет число выше или ниже 50?",
            reply_markup=highlow_keyboard()
        )
    elif game == "slots":
        await state.set_state(GameStates.playing_slots)
        await message.answer(
            f"🎰 *Слоты*\n\nСтавка: *{bet}* {sym}\n\n"
            f"Выигрыши:\n🍒-x2 | 🍋-x3 | 🍊-x4\n🍇-x5 | ⭐-x10 | 💎-x25 | 7️⃣-x50",
            reply_markup=slots_keyboard()
        )
    elif game == "mines":
        game_state = Mines.create_game(num_mines=5)
        await state.update_data(mines_game=game_state)
        await state.set_state(GameStates.playing_mines)
        await message.answer(
            f"💣 *Мины*\n\nСтавка: *{bet}* {sym}\nМин: *5*\n\n"
            f"Открывайте ячейки и избегайте мин!\nМожно забрать выигрыш в любой момент.",
            reply_markup=mines_keyboard(game_state)
        )


# ── Монетка ──────────────────────────────────────────────────
@dp.callback_query(GameStates.playing_coinflip, F.data.startswith("flip_"))
async def play_coinflip(callback: CallbackQuery, state: FSMContext):
    choice   = callback.data.replace("flip_", "")
    data     = await state.get_data()
    bet      = data["bet"]
    currency = data["currency"]
    sym      = currency_symbol(currency)
    user_id  = callback.from_user.id

    db.update_balance(user_id, currency, -bet)
    outcome = CoinFlip.play(bet, choice)

    if outcome.result == GameResult.WIN:
        db.update_balance(user_id, currency, outcome.win_amount)

    db.add_game_record(user_id, "coinflip", bet, currency,
                       outcome.result.value, outcome.win_amount, outcome.game_data)

    result_label = "🌕 Орёл" if outcome.game_data["result"] == "heads" else "🌑 Решка"
    choice_label = "🌕 Орёл" if choice == "heads" else "🌑 Решка"

    if outcome.result == GameResult.WIN:
        text = (f"🎉 *ПОБЕДА!*\n\nВыпало: {result_label}\nВаш выбор: {choice_label}\n\n"
                f"💰 Выигрыш: *{outcome.win_amount:.2f}* {sym}")
    else:
        text = f"😔 *Проигрыш*\n\nВыпало: {result_label}\nВаш выбор: {choice_label}"

    await state.clear()
    await callback.message.edit_text(text, reply_markup=play_again_keyboard("coinflip"))


# ── Кости ────────────────────────────────────────────────────
@dp.callback_query(GameStates.playing_dice, F.data.startswith("dice_"))
async def play_dice(callback: CallbackQuery, state: FSMContext):
    guess    = int(callback.data.replace("dice_", ""))
    data     = await state.get_data()
    bet      = data["bet"]
    currency = data["currency"]
    sym      = currency_symbol(currency)
    user_id  = callback.from_user.id

    db.update_balance(user_id, currency, -bet)
    outcome = Dice.play(bet, guess)

    if outcome.result == GameResult.WIN:
        db.update_balance(user_id, currency, outcome.win_amount)

    db.add_game_record(user_id, "dice", bet, currency,
                       outcome.result.value, outcome.win_amount, outcome.game_data)

    dice_emojis = ["", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    result = outcome.game_data["result"]

    if outcome.result == GameResult.WIN:
        text = (f"🎉 *ПОБЕДА!*\n\n🎲 Выпало: {dice_emojis[result]} ({result})\n"
                f"Ваш выбор: {guess}\n\n💰 Выигрыш: *{outcome.win_amount:.2f}* {sym}")
    else:
        text = (f"😔 *Проигрыш*\n\n🎲 Выпало: {dice_emojis[result]} ({result})\n"
                f"Ваш выбор: {guess}")

    await state.clear()
    await callback.message.edit_text(text, reply_markup=play_again_keyboard("dice"))


# ── High / Low ───────────────────────────────────────────────
@dp.callback_query(GameStates.playing_highlow, F.data.startswith("hl_"))
async def play_highlow(callback: CallbackQuery, state: FSMContext):
    choice   = callback.data.replace("hl_", "")
    data     = await state.get_data()
    bet      = data["bet"]
    currency = data["currency"]
    sym      = currency_symbol(currency)
    user_id  = callback.from_user.id

    db.update_balance(user_id, currency, -bet)
    outcome = HighLow.play(bet, choice)

    if outcome.result in (GameResult.WIN, GameResult.DRAW):
        db.update_balance(user_id, currency, outcome.win_amount)

    db.add_game_record(user_id, "highlow", bet, currency,
                       outcome.result.value, outcome.win_amount, outcome.game_data)

    number       = outcome.game_data["number"]
    choice_label = "📈 Выше" if choice == "high" else "📉 Ниже"

    if outcome.result == GameResult.WIN:
        text = (f"🎉 *ПОБЕДА!*\n\nЧисло: *{number}*\nВаш выбор: {choice_label} 50\n\n"
                f"💰 Выигрыш: *{outcome.win_amount:.2f}* {sym}")
    elif outcome.result == GameResult.DRAW:
        text = f"🤝 *Ничья!*\n\nЧисло: *{number}* (ровно 50)\n\n↩️ Ставка возвращена"
    else:
        text = f"😔 *Проигрыш*\n\nЧисло: *{number}*\nВаш выбор: {choice_label} 50"

    await state.clear()
    await callback.message.edit_text(text, reply_markup=play_again_keyboard("highlow"))


# ── Слоты ────────────────────────────────────────────────────
@dp.callback_query(GameStates.playing_slots, F.data == "spin_slots")
async def play_slots(callback: CallbackQuery, state: FSMContext):
    data     = await state.get_data()
    bet      = data["bet"]
    currency = data["currency"]
    sym      = currency_symbol(currency)
    user_id  = callback.from_user.id

    db.update_balance(user_id, currency, -bet)
    outcome = Slots.play(bet)

    if outcome.result == GameResult.WIN:
        db.update_balance(user_id, currency, outcome.win_amount)

    db.add_game_record(user_id, "slots", bet, currency,
                       outcome.result.value, outcome.win_amount, outcome.game_data)

    grid_display = outcome.game_data["display"]

    if outcome.result == GameResult.WIN:
        wins_text = "\n".join(f"{w[0]} x{w[1]}" for w in outcome.game_data["wins"])
        text = (f"🎰 *СЛОТЫ*\n\n```\n{grid_display}\n```\n\n"
                f"🎉 *ПОБЕДА!*\nЛинии:\n{wins_text}\n\n"
                f"💰 Выигрыш: *{outcome.win_amount:.2f}* {sym}")
    else:
        text = f"🎰 *СЛОТЫ*\n\n```\n{grid_display}\n```\n\n😔 *Нет выигрышных линий*"

    await state.clear()
    await callback.message.edit_text(text, reply_markup=play_again_keyboard("slots"))


# ── Мины ─────────────────────────────────────────────────────
@dp.callback_query(GameStates.playing_mines, F.data.startswith("mine_"))
async def reveal_mine_cell(callback: CallbackQuery, state: FSMContext):
    cell       = int(callback.data.replace("mine_", ""))
    data       = await state.get_data()
    game_state = data["mines_game"]
    bet        = data["bet"]
    currency   = data["currency"]
    sym        = currency_symbol(currency)
    user_id    = callback.from_user.id

    if game_state["game_over"] or cell in game_state["revealed"]:
        await callback.answer("Ячейка уже открыта или игра окончена")
        return

    is_safe, multiplier = Mines.reveal_cell(game_state, cell)

    if is_safe:
        await state.update_data(mines_game=game_state)
        await callback.message.edit_reply_markup(reply_markup=mines_keyboard(game_state))
        await callback.answer(f"💎 Безопасно! Множитель: x{multiplier}")
    else:
        db.update_balance(user_id, currency, -bet)
        db.add_game_record(user_id, "mines", bet, currency, "lose", 0, game_state)
        await state.clear()
        await callback.message.edit_text(
            f"💥 *БУМ! Вы попали на мину!*\n\nПроигрыш: *{bet}* {sym}",
            reply_markup=play_again_keyboard("mines")
        )

@dp.callback_query(GameStates.playing_mines, F.data == "mines_cashout")
async def mines_cashout(callback: CallbackQuery, state: FSMContext):
    data       = await state.get_data()
    game_state = data["mines_game"]
    bet        = data["bet"]
    currency   = data["currency"]
    sym        = currency_symbol(currency)
    user_id    = callback.from_user.id

    if not game_state["revealed"]:
        await callback.answer("Откройте хотя бы одну ячейку!")
        return

    win_amount = round(bet * game_state["multiplier"], 2)
    db.update_balance(user_id, currency, win_amount - bet)
    db.add_game_record(user_id, "mines", bet, currency, "win", win_amount, game_state)

    await state.clear()
    await callback.message.edit_text(
        f"💰 *Вы забрали выигрыш!*\n\n"
        f"Открыто ячеек: {len(game_state['revealed'])}\n"
        f"Множитель: x{game_state['multiplier']}\n\n"
        f"💎 Выигрыш: *{win_amount}* {sym}",
        reply_markup=play_again_keyboard("mines")
    )


# ── Депозит Stars ────────────────────────────────────────────
@dp.callback_query(F.data == "deposit")
async def deposit_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 *Пополнение баланса*\n\nВыберите валюту:",
        reply_markup=currency_keyboard()
    )

@dp.callback_query(F.data == "currency_stars", DepositStates.choosing_currency)
async def deposit_stars_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "⭐ *Пополнение Stars*\n\nВыберите сумму:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ 100",  callback_data="deposit_stars_100")],
            [InlineKeyboardButton(text="⭐ 500",  callback_data="deposit_stars_500")],
            [InlineKeyboardButton(text="⭐ 1000", callback_data="deposit_stars_1000")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
        ])
    )

@dp.callback_query(F.data.startswith("deposit_stars_"))
async def send_stars_invoice(callback: CallbackQuery):
    amount  = int(callback.data.replace("deposit_stars_", ""))
    user_id = callback.from_user.id
    payload = star_payments.create_invoice_payload(user_id, amount, "deposit")

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Покупка {amount} Stars",
        description=f"Пополнение баланса на {amount} Stars",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label=f"{amount} Stars", amount=amount)]
    )
    await callback.answer()

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment      = message.successful_payment
    payload_data = star_payments.parse_invoice_payload(payment.invoice_payload)
    user_id      = payload_data["user_id"]
    amount       = payload_data["amount"]

    db.update_balance(user_id, "stars", amount)
    db.add_transaction(user_id, "deposit", "stars", amount, "completed",
                       telegram_payment_id=payment.telegram_payment_charge_id)

    await message.answer(
        f"✅ *Успешно!*\n\nНа ваш баланс зачислено: ⭐ *{amount}* Stars",
        reply_markup=main_menu_keyboard()
    )


# ── Навигация ────────────────────────────────────────────────
@dp.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎰 *Главное меню*\n\nВыберите действие:",
        reply_markup=main_menu_keyboard()
    )

@dp.callback_query(F.data == "back_games")
async def back_to_games(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GameStates.choosing_game)
    await callback.message.edit_text(
        "🎮 *Выберите игру:*",
        reply_markup=games_keyboard()
    )

@dp.callback_query(F.data == "cancel_game")
async def cancel_game(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Игра отменена\n\nВыберите действие:",
        reply_markup=main_menu_keyboard()
    )

@dp.callback_query(F.data == "withdraw")
async def withdraw_menu(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"💸 *Вывод средств*\n\n"
        f"⭐ Stars: *{user['stars_balance']}*\n"
        f"💎 TON: *{user['ton_balance']:.2f}*\n\n"
        f"Для вывода напишите в поддержку: @support",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
        ])
    )


# ── Запуск ───────────────────────────────────────────────────
async def main():
    logger.info("Bot started...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
