import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# ===================== НАСТРОЙКИ =====================
TOKEN = "8680466852:AAGlGmoqRCFOjJsXxk6s7wNWfWV45ylyu3I"
ADMIN_ID = 8027714217

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# ===================== Корзина (в памяти) =====================
user_cart = {}  # {user_id: [list of services]}

# ===================== FSM =====================
class ProjectForm(StatesGroup):
    waiting_contact = State()

# ===================== Главное меню =====================
def get_main_menu():
    kb = [
        [InlineKeyboardButton(text="🛠 Услуги", callback_data="services"),
         InlineKeyboardButton(text="👑 О нас", callback_data="about")],
        [InlineKeyboardButton(text="⚡ Процесс", callback_data="process"),
         InlineKeyboardButton(text="💰 Цены", callback_data="prices")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
         InlineKeyboardButton(text="💎 Оформить заявку", callback_data="start_project")],
        [InlineKeyboardButton(text="📞 Связаться", callback_data="contact")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ===================== Добавление в корзину =====================
def add_to_cart(user_id, service):
    if user_id not in user_cart:
        user_cart[user_id] = []
    if service not in user_cart[user_id]:
        user_cart[user_id].append(service)

# ===================== Показ корзины =====================
def show_cart(user_id):
    if user_id not in user_cart or not user_cart[user_id]:
        return "🛒 Ваша корзина пуста.\n\nДобавляйте услуги из раздела «Цены»."
    
    items = "\n".join([f"• {item}" for item in user_cart[user_id]])
    return f"🛒 <b>Ваша корзина</b>\n\n{items}\n\nНажмите «Оформить заявку», чтобы продолжить."

# ===================== /start =====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "✺ <b>Luce.</b>\n\n"
        "Цифровой люкс нового поколения.\n"
        "Мы создаём премиальные продукты по очень приятным ценам.\n\n"
        "Выберите раздел:",
        reply_markup=get_main_menu()
    )

# ===================== ЦЕНЫ (максимально расширенный и живой раздел) =====================
@dp.callback_query(F.data == "prices")
async def show_prices(call: types.CallbackQuery):
    text = (
        "💰 <b>Цены Luce. — максимально доступный люкс</b>\n\n"
        "Мы сделали цены очень привлекательными, чтобы вы могли позволить себе качественный цифровой продукт.\n\n"
        
        "<b>Telegram-боты</b>\n"
        "• Простой бот — <b>1 000 ₽</b>\n"
        "• Средний бот (с базой данных) — <b>2 000 ₽</b>\n"
        "• Тяжёлый / магазинный бот — <b>3 000 ₽</b>\n\n"
        
        "<b>Сайты</b>\n"
        "• Сайт-визитка — <b>1 000 ₽</b>\n"
        "• Лендинг / продающий сайт — <b>2 000 ₽</b>\n"
        "• Корпоративный сайт — <b>5 000 ₽</b>\n"
        "• Интернет-магазин — <b>8 000 ₽</b>\n\n"
        
        "<b>Мобильные приложения</b>\n"
        "• Простое приложение — <b>2 000 ₽</b>\n"
        "• Полноценное приложение (iOS + Android) — <b>8 000 ₽</b>\n\n"
        
        "Нажмите на услугу ниже, чтобы добавить её в корзину 👇"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Простой бот — 1 000 ₽", callback_data="add_bot_simple")],
        [InlineKeyboardButton(text="🤖 Средний бот — 2 000 ₽", callback_data="add_bot_medium")],
        [InlineKeyboardButton(text="🤖 Тяжёлый бот — 3 000 ₽", callback_data="add_bot_hard")],
        [InlineKeyboardButton(text="🌐 Сайт-визитка — 1 000 ₽", callback_data="add_site_visitka")],
        [InlineKeyboardButton(text="🌐 Лендинг — 2 000 ₽", callback_data="add_site_landing")],
        [InlineKeyboardButton(text="🌐 Корпоративный сайт — 5 000 ₽", callback_data="add_site_corp")],
        [InlineKeyboardButton(text="🌐 Интернет-магазин — 8 000 ₽", callback_data="add_site_shop")],
        [InlineKeyboardButton(text="📱 Простое приложение — 2 000 ₽", callback_data="add_app_simple")],
        [InlineKeyboardButton(text="📱 Полноценное приложение — 8 000 ₽", callback_data="add_app_full")],
        [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="cart")]
    ])

    await call.message.edit_text(text, reply_markup=kb)

# ===================== Добавление в корзину =====================
@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    service_map = {
        "add_bot_simple": "🤖 Простой Telegram-бот — 1 000 ₽",
        "add_bot_medium": "🤖 Средний Telegram-бот — 2 000 ₽",
        "add_bot_hard": "🤖 Тяжёлый Telegram-бот — 3 000 ₽",
        "add_site_visitka": "🌐 Сайт-визитка — 1 000 ₽",
        "add_site_landing": "🌐 Лендинг — 2 000 ₽",
        "add_site_corp": "🌐 Корпоративный сайт — 5 000 ₽",
        "add_site_shop": "🌐 Интернет-магазин — 8 000 ₽",
        "add_app_simple": "📱 Простое мобильное приложение — 2 000 ₽",
        "add_app_full": "📱 Полноценное приложение — 8 000 ₽",
    }
    
    service = service_map.get(call.data)
    if service:
        add_to_cart(user_id, service)
        await call.answer("✅ Добавлено в корзину!", show_alert=True)
    await call.message.edit_text("Добавлено в корзину! 👇", reply_markup=get_main_menu())

# ===================== Корзина =====================
@dp.callback_query(F.data == "cart")
async def show_cart_handler(call: types.CallbackQuery):
    text = show_cart(call.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Оформить заявку", callback_data="start_project")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: types.CallbackQuery):
    await call.message.edit_text("✺ <b>Luce.</b>\n\nВыберите раздел:", reply_markup=get_main_menu())

# ===================== Остальные разделы (живые) =====================
@dp.callback_query(F.data == "services")
async def show_services(call: types.CallbackQuery):
    text = (
        "🛠 <b>Наши услуги</b>\n\n"
        "Мы создаём цифровые продукты, которые выглядят дорого, но стоят очень приятно.\n\n"
        "• Премиальные сайты и лендинги\n"
        "• Умные Telegram-боты\n"
        "• Мобильные приложения\n"
        "• Полный цифровой брендинг"
    )
    await call.message.edit_text(text, reply_markup=get_main_menu())

@dp.callback_query(F.data == "about")
async def show_about(call: types.CallbackQuery):
    text = (
        "👑 <b>О нас — Luce.</b>\n\n"
        "Мы молодая, но очень амбициозная студия цифровой роскоши.\n"
        "Наша цель — делать качественные продукты по максимально доступным ценам.\n\n"
        "Уже сейчас мы помогаем людям и бизнесам получать красивые и рабочие решения."
    )
    await call.message.edit_text(text, reply_markup=get_main_menu())

@dp.callback_query(F.data == "process")
async def show_process(call: types.CallbackQuery):
    text = (
        "⚡ <b>Как мы работаем</b>\n\n"
        "Всё максимально просто и прозрачно:\n"
        "1. Вы описываете идею\n"
        "2. Мы обсуждаем детали\n"
        "3. Делаем вам крутой продукт\n"
        "4. Вы получаете готовое решение"
    )
    await call.message.edit_text(text, reply_markup=get_main_menu())

@dp.callback_query(F.data == "contact")
async def show_contact(call: types.CallbackQuery):
    text = "📞 <b>Связаться с нами</b>\n\nПросто нажмите «Оформить заявку» — это самый быстрый способ."
    await call.message.edit_text(text, reply_markup=get_main_menu())

# ===================== Оформление заявки =====================
@dp.callback_query(F.data == "start_project")
async def start_project(call: types.CallbackQuery, state: FSMContext):
    cart_text = show_cart(call.from_user.id)
    if "пуста" in cart_text:
        await call.answer("Корзина пуста! Добавьте что-нибудь из раздела Цены.", show_alert=True)
        return
    
    await call.message.edit_text(
        f"{cart_text}\n\nНапишите ваши контакты (имя + Telegram или телефон), и мы сразу свяжемся с вами."
    )
    await state.set_state(ProjectForm.waiting_contact)

@dp.message(ProjectForm.waiting_contact)
async def process_contact(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cart = user_cart.get(user_id, [])

    final_text = (
        f"📨 <b>НОВАЯ ЗАЯВКА С КОРЗИНОЙ</b>\n\n"
        f"👤 {message.from_user.first_name} (@{message.from_user.username or 'нет'})\n"
        f"🆔 {message.from_user.id}\n\n"
        f"🛒 Выбрано:\n" + "\n".join([f"• {item}" for item in cart]) + f"\n\n"
        f"📞 Контакты: {message.text}"
    )

    await bot.send_message(ADMIN_ID, final_text)
    await message.answer("✅ Заявка успешно отправлена!\nМы свяжемся с вами очень скоро.", reply_markup=get_main_menu())
    
    # Очищаем корзину после отправки
    if user_id in user_cart:
        del user_cart[user_id]
    await state.clear()

# ===================== Запуск =====================
async def main():
    print("🚀 Бот Luce. успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
