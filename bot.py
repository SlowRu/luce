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

from config import config
from database import db
from games import CoinFlip, Dice, HighLow, Slots, Mines, GameResult
from payments import star_payments, ton_payments

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM States
class GameStates(StatesGroup):
    choosing_game = State()
    choosing_currency = State()
    entering_bet = State()
    playing_coinflip = State()
    playing_dice = State()
    playing_highlow = State()
    playing_slots = State()
    playing_mines = State()

class DepositStates(StatesGroup):
    choosing_currency = State()
    entering_amount = State()
    waiting_payment = State()

# Клавиатуры
def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data="play")],
        [InlineKeyboardButton(text="💰 Депозит", callback_data="deposit"),
         InlineKeyboardButton(text="💸 Вывод", callback_data="withdraw")],
        [InlineKeyboardButton(text="👛 Баланс", callback_data="balance"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
    ])

def games_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Монетка", callback_data="game_coinflip"),
         InlineKeyboardButton(text="🎲 Кости", callback_data="game_dice")],
        [InlineKeyboardButton(text="📈 High/Low", callback_data="game_highlow"),
         InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots")],
        [InlineKeyboardButton(text="💣 Мины", callback_data="game_mines")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
    ])

def currency_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Stars", callback_data="currency_stars"),
         InlineKeyboardButton(text="💎 TON", callback_data="currency_ton")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_games")]
    ])

def coinflip_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌕 Орёл", callback_data="flip_heads"),
         InlineKeyboardButton(text="🌑 Решка", callback_data="flip_tails")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_game")]
    ])

def dice_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"dice_{i}") for i in range(1, 4)],
        [InlineKeyboardButton(text=str(i), callback_data=f"dice_{i}") for i in range(4, 7)],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_game")]
    ])

def highlow_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Выше 50", callback_data="hl_high"),
         InlineKeyboardButton(text="📉 Ниже 50", callback_data="hl_low")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_game")]
    ])

def slots_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Крутить!", callback_data="spin_slots")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_games")]
    ])

def mines_keyboard(game_state: dict):
    revealed = set(game_state['revealed'])
    mines = set(game_state['mines']) if game_state['game_over'] else set()
    
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
        InlineKeyboardButton(text=f"💰 Забрать (x{game_state['multiplier']})", 
                            callback_data="mines_cashout"),
        InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_game")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Handlers
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    db.create_user(user_id, username)
    
    await message.answer(
        f"🎰 *Добро пожаловать в Game Bot!*\n\n"
        f"Здесь вы можете играть в азартные игры на:\n"
        f"⭐ Telegram Stars\n"
        f"💎 TON\n\n"
        f"Выберите действие:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

@dp.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        db.create_user(user_id)
        user = db.get_user(user_id)
    
    await callback.message.edit_text(
        f"👛 *Ваш баланс:*\n\n"
        f"⭐ Stars: *{user['stars_balance']}*\n"
        f"💎 TON: *{user['ton_balance']:.2f}*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
        ])
    )

@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("Статистика недоступна")
        return
    
    win_rate = (user['total_wins'] / user['total_games'] * 100) if user['total_games'] > 0 else 0
    
    await callback.message.edit_text(
        f"📊 *Ваша статистика:*\n\n"
        f"🎮 Всего игр: *{user['total_games']}*\n"
        f"🏆 Побед: *{user['total_wins']}*\n"
        f"📈 Винрейт: *{win_rate:.1f}%*\n\n"
        f"💰 Поставлено Stars: *{user['total_wagered_stars']}*\n"
        f"💎 Поставлено TON: *{user['total_wagered_ton']:.2f}*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
        ])
    )

@dp.callback_query(F.data == "play")
async def choose_game(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GameStates.choosing_game)
    await callback.message.edit_text(
        "🎮 *Выберите игру:*\n\n"
        "🪙 *Монетка* - угадай сторону (x1.9)\n"
        "🎲 *Кости* - угадай число (x5.7)\n"
        "📈 *High/Low* - выше или ниже 50 (x1.9)\n"
        "🎰 *Слоты* - классические слоты (до x50)\n"
        "💣 *Мины* - открывай безопасные ячейки",
        parse_mode="Markdown",
        reply_markup=games_keyboard()
    )

@dp.callback_query(F.data.startswith("game_"))
async def select_game(callback: CallbackQuery, state: FSMContext):
    game = callback.data.replace("game_", "")
    await state.update_data(selected_game=game)
    await state.set_state(GameStates.choosing_currency)
    
    await callback.message.edit_text(
        "💰 *Выберите валюту для ставки:*",
        parse_mode="Markdown",
        reply_markup=currency_keyboard()
    )

@dp.callback_query(F.data.startswith("currency_"))
async def select_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.replace("currency_", "")
    await state.update_data(currency=currency)
    await state.set_state(GameStates.entering_bet)
    
    user_id = callback.from_user.id
    balance = db.get_balance(user_id, currency)
    
    currency_symbol = "⭐" if currency == "stars" else "💎"
    min_bet = config.MIN_BET_STARS if currency == "stars" else config.MIN_BET_TON
    max_bet = config.MAX_BET_STARS if currency == "stars" else config.MAX_BET_TON
    
    await callback.message.edit_text(
        f"💰 *Введите сумму ставки*\n\n"
        f"Ваш баланс: {currency_symbol} *{balance}*\n"
        f"Мин. ставка: {min_bet}\n"
        f"Макс. ставка: {max_bet}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_game")]
        ])
    )

@dp.message(GameStates.entering_bet)
async def process_bet(message: Message, state: FSMContext):
    try:
        bet = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите корректное число")
        return
    
    data = await state.get_data()
    currency = data['currency']
    game = data['selected_game']
    user_id = message.from_user.id
    
    # Проверки
    min_bet = config.MIN_BET_STARS if currency == "stars" else config.MIN_BET_TON
    max_bet = config.MAX_BET_STARS if currency == "stars" else config.MAX_BET_TON
    balance = db.get_balance(user_id, currency)
    
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
    
    # Показываем интерфейс игры
    if game == "coinflip":
        await state.set_state(GameStates.playing_coinflip)
        await message.answer(
            f"🪙 *Монетка*\n\n"
            f"Ставка: *{bet}* {'⭐' if currency == 'stars' else '💎'}\n"
            f"Выигрыш: *x1.9*\n\n"
            f"Выберите сторону:",
            parse_mode="Markdown",
            reply_markup=coinflip_keyboard()
        )
    
    elif game == "dice":
        await state.set_state(GameStates.playing_dice)
        await message.answer(
            f"🎲 *Кости*\n\n"
            f"Ставка: *{bet}* {'⭐' if currency == 'stars' else '💎'}\n"
            f"Выигрыш: *x5.7*\n\n"
            f"Выберите число от 1 до 6:",
            parse_mode="Markdown",
            reply_markup=dice_keyboard()
        )
    
    elif game == "highlow":
        await state.set_state(GameStates.playing_highlow)
        await message.answer(
            f"📈 *High/Low*\n\n"
            f"Ставка: *{bet}* {'⭐' if currency == 'stars' else '💎'}\n"
            f"Выигрыш: *x1.9*\n\n"
            f"Будет число выше или ниже 50?",
            parse_mode="Markdown",
            reply_markup=highlow_keyboard()
        )
    
    elif game == "slots":
        await state.set_state(GameStates.playing_slots)
        await message.answer(
            f"🎰 *Слоты*\n\n"
            f"Ставка: *{bet}* {'⭐' if currency == 'stars' else '💎'}\n\n"
            f"Выигрыши:\n"
            f"🍒 - x2 | 🍋 - x3 | 🍊 - x4\n"
            f"🍇 - x5 | ⭐ - x10 | 💎 - x25 | 7️⃣ - x50",
            parse_mode="Markdown",
            reply_markup=slots_keyboard()
        )
    
    elif game == "mines":
        game_state = Mines.create_game(num_mines=5)
        await state.update_data(mines_game=game_state)
        await state.set_state(GameStates.playing_mines)
        await message.answer(
            f"💣 *Мины*\n\n"
            f"Ставка: *{bet}* {'⭐' if currency == 'stars' else '💎'}\n"
            f"Мин на поле: *5*\n\n"
            f"Открывайте ячейки и избегайте мин!\n"
            f"Можете забрать выигрыш в любой момент.",
            parse_mode="Markdown",
            reply_markup=mines_keyboard(game_state)
        )

# Обработчики игр
@dp.callback_query(GameStates.playing_coinflip, F.data.startswith("flip_"))
async def play_coinflip(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("flip_", "")
    data = await state.get_data()
    bet = data['bet']
    currency = data['currency']
    user_id = callback.from_user.id
    
    # Списываем ставку
    db.update_balance(user_id, currency, -bet)
    
    # Играем
    outcome = CoinFlip.play(bet, choice)
    
    # Начисляем выигрыш
    if outcome.result == GameResult.WIN:
        db.update_balance(user_id, currency, outcome.win_amount)
    
    # Записываем в историю
    db.add_game_record(
        user_id, 'coinflip', bet, currency,
        outcome.result.value, outcome.win_amount, outcome.game_data
    )
    
    # Формируем ответ
    result_emoji = "🌕 Орёл" if outcome.game_data['result'] == 'heads' else "🌑 Решка"
    
    if outcome.result == GameResult.WIN:
        text = (
            f"🎉 *ПОБЕДА!*\n\n"
            f"Выпало: {result_emoji}\n"
            f"Ваш выбор: {'🌕 Орёл' if choice == 'heads' else '🌑 Решка'}\n\n"
            f"💰 Выигрыш: *{outcome.win_amount:.2f}* {'⭐' if currency == 'stars' else '💎'}"
        )
    else:
        text = (
            f"😔 *Проигрыш*\n\n"
            f"Выпало: {result_emoji}\n"
            f"Ваш выбор: {'🌕 Орёл' if choice == 'heads' else '🌑 Решка'}"
        )
    
    await state.clear()
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Играть снова", callback_data="game_coinflip")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])
    )

@dp.callback_query(GameStates.playing_dice, F.data.startswith("dice_"))
async def play_dice(callback: CallbackQuery, state: FSMContext):
    guess = int(callback.data.replace("dice_", ""))
    data = await state.get_data()
    bet = data['bet']
    currency = data['currency']
    user_id = callback.from_user.id
    
    db.update_balance(user_id, currency, -bet)
    outcome = Dice.play(bet, guess)
    
    if outcome.result == GameResult.WIN:
        db.update_balance(user_id, currency, outcome.win_amount)
    
    db.add_game_record(
        user_id, 'dice', bet, currency,
        outcome.result.value, outcome.win_amount, outcome.game_data
    )
    
    dice_emojis = ['', '⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    result = outcome.game_data['result']
    
    if outcome.result == GameResult.WIN:
        text = (
            f"🎉 *ПОБЕДА!*\n\n"
            f"🎲 Выпало: {dice_emojis[result]} ({result})\n"
            f"Ваш выбор: {guess}\n\n"
            f"💰 Выигрыш: *{outcome.win_amount:.2f}* {'⭐' if currency == 'stars' else '💎'}"
        )
    else:
        text = (
            f"😔 *Проигрыш*\n\n"
            f"🎲 Выпало: {dice_emojis[result]} ({result})\n"
            f"Ваш выбор: {guess}"
        )
    
    await state.clear()
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Играть снова", callback_data="game_dice")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])
    )

@dp.callback_query(GameStates.playing_highlow, F.data.startswith("hl_"))
async def play_highlow(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("hl_", "")
    data = await state.get_data()
    bet = data['bet']
    currency = data['currency']
    user_id = callback.from_user.id
    
    db.update_balance(user_id, currency, -bet)
    outcome = HighLow.play(bet, choice)
    
    if outcome.result in [GameResult.WIN, GameResult.DRAW]:
        db.update_balance(user_id, currency, outcome.win_amount)
    
    db.add_game_record(
        user_id, 'highlow', bet, currency,
        outcome.result.value, outcome.win_amount, outcome.game_data
    )
    
    number = outcome.game_data['number']
    
    if outcome.result == GameResult.WIN:
        text = (
            f"🎉 *ПОБЕДА!*\n\n"
            f"Число: *{number}*\n"
            f"Ваш выбор: {'📈 Выше' if choice == 'high' else '📉 Ниже'} 50\n\n"
            f"💰 Выигрыш: *{outcome.win_amount:.2f}* {'⭐' if currency == 'stars' else '💎'}"
        )
    elif outcome.result == GameResult.DRAW:
        text = (
            f"🤝 *Ничья!*\n\n"
            f"Число: *{number}* (ровно 50)\n\n"
            f"↩️ Ставка возвращена"
        )
    else:
        text = (
            f"😔 *Проигрыш*\n\n"
            f"Число: *{number}*\n"
            f"Ваш выбор: {'📈 Выше' if choice == 'high' else '📉 Ниже'} 50"
        )
    
    await state.clear()
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Играть снова", callback_data="game_highlow")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])
    )

@dp.callback_query(GameStates.playing_slots, F.data == "spin_slots")
async def play_slots(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bet = data['bet']
    currency = data['currency']
    user_id = callback.from_user.id
    
    db.update_balance(user_id, currency, -bet)
    outcome = Slots.play(bet)
    
    if outcome.result == GameResult.WIN:
        db.update_balance(user_id, currency, outcome.win_amount)
    
    db.add_game_record(
        user_id, 'slots', bet, currency,
        outcome.result.value, outcome.win_amount, outcome.game_data
    )
    
    grid_display = outcome.game_data['display']
    
    if outcome.result == GameResult.WIN:
        wins_text = "\n".join([f"{w[0]} x{w[1]}" for w in outcome.game_data['wins']])
        text = (
            f"🎰 *СЛОТЫ*\n\n"
            f"```\n{grid_display}\n```\n\n"
            f"🎉 *ПОБЕДА!*\n"
            f"Линии: {wins_text}\n\n"
            f"💰 Выигрыш: *{outcome.win_amount:.2f}* {'⭐' if currency == 'stars' else '💎'}"
        )
    else:
        text = (
            f"🎰 *СЛОТЫ*\n\n"
            f"```\n{grid_display}\n```\n\n"
            f"😔 *Нет выигрышных линий*"
        )
    
    await state.clear()
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Крутить снова", callback_data="game_slots")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])
    )

@dp.callback_query(GameStates.playing_mines, F.data.startswith("mine_"))
async def reveal_mine_cell(callback: CallbackQuery, state: FSMContext):
    cell = int(callback.data.replace("mine_", ""))
    data = await state.get_data()
    game_state = data['mines_game']
    bet = data['bet']
    currency = data['currency']
    user_id = callback.from_user.id
    
    if game_state['game_over'] or cell in game_state['revealed']:
        await callback.answer("Ячейка уже открыта или игра окончена")
        return
    
    is_safe, multiplier = Mines.reveal_cell(game_state, cell)
    
    if is_safe:
        await state.update_data(mines_game=game_state)
        await callback.message.edit_reply_markup(reply_markup=mines_keyboard(game_state))
        await callback.answer(f"💎 Безопасно! Множитель: x{multiplier}")
    else:
        # Проигрыш - списываем ставку
        db.update_balance(user_id, currency, -bet)
        db.add_game_record(
            user_id, 'mines', bet, currency,
            'lose', 0, game_state
        )
        
        await state.clear()
        await callback.message.edit_text(
            f"💥 *БУМ! Вы попали на мину!*\n\n"
            f"Проигрыш: *{bet}* {'⭐' if currency == 'stars' else '💎'}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Играть снова", callback_data="game_mines")],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
            ])
        )

@dp.callback_query(GameStates.playing_mines, F.data == "mines_cashout")
async def mines_cashout(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    game_state = data['mines_game']
    bet = data['bet']
    currency = data['currency']
    user_id = callback.from_user.id
    
    if not game_state['revealed']:
        await callback.answer("Откройте хотя бы одну ячейку!")
        return
    
    win_amount = bet * game_state['multiplier']
    
    # Начисляем выигрыш (ставка не списывается заранее в минах)
    db.update_balance(user_id, currency, win_amount - bet)
    db.add_game_record(
        user_id, 'mines', bet, currency,
        'win', win_amount, game_state
    )
    
    await state.clear()
    await callback.message.edit_text(
        f"💰 *Вы забрали выигрыш!*\n\n"
        f"Открыто ячеек: {len(game_state['revealed'])}\n"
        f"Множитель: x{game_state['multiplier']}\n\n"
        f"💎 Выигрыш: *{win_amount:.2f}* {'⭐' if currency == 'stars' else '💎'}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Играть снова", callback_data="game_mines")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])
    )

# Депозиты
@dp.callback_query(F.data == "deposit")
async def deposit_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DepositStates.choosing_currency)
    await callback.message.edit_text(
        "💰 *Пополнение баланса*\n\n"
        "Выберите валюту:",
        parse_mode="Markdown",
        reply_markup=currency_keyboard()
    )

@dp.callback_query(DepositStates.choosing_currency, F.data.startswith("currency_"))
async def deposit_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.replace("currency_", "")
    await state.update_data(currency=currency)
    await state.set_state(DepositStates.entering_amount)
    
    if currency == "stars":
        # Для Stars используем Telegram Payments
        await callback.message.edit_text(
            "⭐ *Пополнение Stars*\n\n"
            "Выберите сумму пополнения:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ 100 Stars", callback_data="deposit_stars_100")],
                [InlineKeyboardButton(text="⭐ 500 Stars", callback_data="deposit_stars_500")],
                [InlineKeyboardButton(text="⭐ 1000 Stars", callback_data="deposit_stars_1000")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
            ])
        )
    else:
        # Для TON показываем адрес кошелька
        memo = ton_payments.generate_payment_memo(callback.from_user.id)
        await state.update_data(ton_memo=memo)
        
        await callback.message.edit_text(
            f"💎 *Пополнение TON*\n\n"
            f"Отправьте TON на кошелёк:\n"
            f"`{config.TON_WALLET}`\n\n"
            f"⚠️ Обязательно укажите в комментарии:\n"
            f"`{memo}`\n\n"
            f"После отправки нажмите кнопку проверки.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Проверить платёж", callback_data="check_ton_payment")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
            ])
        )

@dp.callback_query(F.data.startswith("deposit_stars_"))
async def send_stars_invoice(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.replace("deposit_stars_", ""))
    user_id = callback.from_user.id
    
    payload = star_payments.create_invoice_payload(user_id, amount, "deposit")
    
    # Создаём инвойс для Telegram Stars
    prices = [LabeledPrice(label=f"{amount} Stars", amount=amount)]
    
    await callback.message.answer_invoice(
        title=f"Покупка {amount} Stars",
        description=f"Пополнение баланса на {amount} Stars для игры",
        payload=payload,
        currency="XTR",  # Telegram Stars
        prices=prices
    )
    await callback.answer()

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment = message.successful_payment
    payload_data = star_payments.parse_invoice_payload(payment.invoice_payload)
    
    user_id = payload_data['user_id']
    amount = payload_data['amount']
    
    # Начисляем Stars
    db.update_balance(user_id, 'stars', amount)
    db.add_transaction(
        user_id, 'deposit', 'stars', amount, 'completed',
        telegram_payment_id=payment.telegram_payment_charge_id
    )
    
    await message.answer(
        f"✅ *Успешно!*\n\n"
        f"На ваш баланс зачислено: ⭐ *{amount}* Stars",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

@dp.callback_query(F.data == "check_ton_payment")
async def check_ton_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    memo = data.get('ton_memo')
    
    if not memo:
        await callback.answer("Ошибка: memo не найден")
        return
    
    # Проверяем платёж (упрощённая логика)
    await callback.answer("🔍 Проверяем платёж...", show_alert=True)
    
    # В реальном боте здесь нужна проверка через API
    # found = await ton_payments.check_payment(amount, memo)
    
    await callback.message.edit_text(
        "⏳ *Платёж обрабатывается*\n\n"
        "Обычно это занимает 1-5 минут.\n"
        "После подтверждения баланс будет обновлён автоматически.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Проверить снова", callback_data="check_ton_payment")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])
    )

# Навигация
@dp.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎰 *Главное меню*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

@dp.callback_query(F.data == "back_games")
async def back_to_games(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GameStates.choosing_game)
    await callback.message.edit_text(
        "🎮 *Выберите игру:*",
        parse_mode="Markdown",
        reply_markup=games_keyboard()
    )

@dp.callback_query(F.data == "cancel_game")
async def cancel_game(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Игра отменена\n\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard()
    )

# Запуск
async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
