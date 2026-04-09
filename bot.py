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

# ===================== FSM =====================
class ProjectForm(StatesGroup):
    waiting_description = State()
    waiting_budget = State()
    waiting_contact = State()

# ===================== Главное меню =====================
def get_main_menu():
    kb = [
        [InlineKeyboardButton(text="🛠 Услуги", callback_data="services"),
         InlineKeyboardButton(text="👑 О нас", callback_data="about")],
        [InlineKeyboardButton(text="⚡ Процесс", callback_data="process"),
         InlineKeyboardButton(text="💰 Цены", callback_data="prices")],
        [InlineKeyboardButton(text="💎 Начать проект", callback_data="start_project"),
         InlineKeyboardButton(text="📞 Связаться", callback_data="contact")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ===================== Умное распознавание категории =====================
def detect_category(text: str):
    text = text.lower()
    
    bot_keywords = ["бот", "bots", "telegram", "тг", "tg", "bot", "бота", "боты", "телеграм"]
    site_keywords = ["сайт", "сайты", "landing", "лендинг", "визитка", "магазин", "web", "website", "интернет-магазин"]
    app_keywords = ["приложение", "приложения", "app", "apps", "мобильное", "android", "ios", "мобил", "приложение"]

    if any(word in text for word in bot_keywords):
        return "bots"
    if any(word in text for word in site_keywords):
        return "sites"
    if any(word in text for word in app_keywords):
        return "apps"
    
    return None

# ===================== /start =====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = "✺ <b>Luce.</b>\n\nЦифровой люкс нового поколения.\n\nВыберите раздел:"
    await message.answer(text, reply_markup=get_main_menu())

# ===================== Начать проект =====================
@dp.callback_query(F.data == "start_project")
async def start_project(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "💎 <b>Начать проект</b>\n\n"
        "Опишите вашу идею. Например:\n"
        "«бот стихоплет», «сайт пугалка», «мобильное приложение для записей»"
    )
    await state.set_state(ProjectForm.waiting_description)

# ===================== Умная обработка описания =====================
@dp.message(ProjectForm.waiting_description)
async def process_description(message: types.Message, state: FSMContext):
    category = detect_category(message.text)

    if category == "bots":
        text = (
            "🤖 <b>Вы ищете Telegram-бота</b>\n\n"
            "Цены на ботов:\n"
            "• Простой бот — <b>от 1 000 ₽</b>\n"
            "• Средний бот — <b>от 2 000 ₽</b>\n"
            "• Сложный бот / магазин — <b>от 3 490 ₽</b>\n\n"
        )
    elif category == "sites":
        text = (
            "🌐 <b>Вы ищете сайт</b>\n\n"
            "Цены на сайты:\n"
            "• Сайт-визитка — <b>от 1 000 ₽</b>\n"
            "• Премиальный лендинг — <b>от 2 000 ₽</b>\n"
            "• Корпоративный сайт — <b>от 3 000 ₽</b>\n"
            "• Интернет-магазин — <b>от 5 000 ₽</b>\n\n"
        )
    elif category == "apps":
        text = (
            "📱 <b>Вы ищете мобильное приложение</b>\n\n"
            "Цены на приложения:\n"
            "• Простое приложение — <b>от 2 000 ₽</b>\n"
            "• Полноценное приложение (iOS + Android) — <b>от 8 000 ₽</b>\n\n"
        )
    else:
        # Если ничего не распознал
        await state.update_data(description=message.text)
        await message.answer("Отлично! Какой у вас примерный бюджет проекта?")
        await state.set_state(ProjectForm.waiting_budget)
        return

    # Если категория определена — показываем цены + кнопку продолжения
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Продолжить оформление заявки", callback_data="continue_form")]
    ])
    await message.answer(text, reply_markup=kb)
    await state.update_data(description=message.text)

# ===================== Продолжение формы =====================
@dp.callback_query(F.data == "continue_form")
async def continue_form(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("Отлично! Какой у вас примерный бюджет проекта?")
    await state.set_state(ProjectForm.waiting_budget)

# ===================== Остальная часть формы =====================
@dp.message(ProjectForm.waiting_budget)
async def process_budget(message: types.Message, state: FSMContext):
    await state.update_data(budget=message.text)
    await message.answer("Последний шаг. Укажите ваши контакты (имя + Telegram или телефон):")
    await state.set_state(ProjectForm.waiting_contact)

@dp.message(ProjectForm.waiting_contact)
async def process_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    final_text = (
        f"📨 <b>НОВАЯ ЗАЯВКА</b>\n\n"
        f"👤 {message.from_user.first_name} (@{message.from_user.username or 'нет'})\n"
        f"🆔 {message.from_user.id}\n\n"
        f"📝 Описание: {data['description']}\n\n"
        f"💰 Бюджет: {data['budget']}\n\n"
        f"📞 Контакты: {message.text}"
    )
    await bot.send_message(ADMIN_ID, final_text)
    await message.answer("✅ Заявка отправлена! Мы свяжемся с вами очень скоро.", reply_markup=get_main_menu())
    await state.clear()

# ===================== Остальные разделы =====================
@dp.callback_query(F.data == "services")
async def show_services(call: types.CallbackQuery):
    text = "🛠 <b>Услуги</b>\n\n• Премиальные сайты\n• Telegram-боты\n• Мобильные приложения\n• Цифровой брендинг"
    await call.message.edit_text(text, reply_markup=get_main_menu())

@dp.callback_query(F.data == "prices")
async def show_prices(call: types.CallbackQuery):
    text = "💰 <b>Цены</b>\n\nПодробные цены смотрите в разделе «Услуги» или нажмите «Начать проект»"
    await call.message.edit_text(text, reply_markup=get_main_menu())

@dp.callback_query(F.data == "about")
async def show_about(call: types.CallbackQuery):
    text = "👑 <b>О нас</b>\n\nLuce. — независимая студия цифровой роскоши."
    await call.message.edit_text(text, reply_markup=get_main_menu())

@dp.callback_query(F.data == "process")
async def show_process(call: types.CallbackQuery):
    text = "⚡ <b>Процесс работы</b>\n\n1. Брифинг\n2. Дизайн\n3. Разработка\n4. Тестирование\n5. Запуск"
    await call.message.edit_text(text, reply_markup=get_main_menu())

@dp.callback_query(F.data == "contact")
async def show_contact(call: types.CallbackQuery):
    text = "📞 <b>Связаться</b>\n\nНапишите нам: mollyhuetonn@gmail.com"
    await call.message.edit_text(text, reply_markup=get_main_menu())

# ===================== Запуск =====================
async def main():
    print("🚀 Бот Luce. успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
