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

# ===================== Умное распознавание =====================
def detect_category(text: str):
    text = text.lower()
    bot_keywords = ["бот", "bots", "telegram", "тг", "tg", "bot", "бота", "боты"]
    site_keywords = ["сайт", "сайты", "landing", "лендинг", "визитка", "магазин", "web", "website"]
    app_keywords = ["приложение", "приложения", "app", "apps", "мобильное", "android", "ios", "мобил"]

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
    await message.answer("✺ <b>Luce.</b>\n\nЦифровой люкс нового поколения.\n\nВыберите раздел:", 
                         reply_markup=get_main_menu())

# ===================== Начать проект =====================
@dp.callback_query(F.data == "start_project")
async def start_project(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "💎 <b>Начать проект</b>\n\n"
        "Опишите вашу идею (например: «бот стихоплет», «сайт пугалка», «мобильное приложение»)"
    )
    await state.set_state(ProjectForm.waiting_description)

# ===================== Обработка описания =====================
@dp.message(ProjectForm.waiting_description)
async def process_description(message: types.Message, state: FSMContext):
    category = detect_category(message.text)

    if category == "bots":
        text = "🤖 <b>Вы ищете Telegram-бота</b>\n\nЦены:\n• Простой — от 1 000 ₽\n• Средний — от 2 000 ₽\n• Сложный — от 3 000 ₽\n\n"
    elif category == "sites":
        text = "🌐 <b>Вы ищете сайт</b>\n\nЦены:\n• Визитка — от 1 000 ₽\n• Лендинг — от 2 000 ₽\n• Корпоративный — от 5 000 ₽\n• Магазин — от 8 000 ₽\n\n"
    elif category == "apps":
        text = "📱 <b>Вы ищете мобильное приложение</b>\n\nЦены:\n• Простое — от 2 000 ₽\n• Полноценное — от 8 000 ₽\n\n"
    else:
        text = ""

    await message.answer(text + "Какой у вас примерный бюджет проекта?")
    await state.update_data(description=message.text)
    await state.set_state(ProjectForm.waiting_budget)

# ===================== Проверка бюджета (главное изменение) =====================
@dp.message(ProjectForm.waiting_budget)
async def process_budget(message: types.Message, state: FSMContext):
    budget_text = message.text.lower().strip()

    # Пытаемся понять число
    import re
    numbers = re.findall(r'\d+', budget_text)
    
    budget_num = 0
    if numbers:
        budget_num = int(numbers[0])

    if budget_num < 1000 and budget_num != 0:
        await message.answer(
            "❌ Минимальный бюджет для проектов — **1000 ₽**.\n\n"
            "Если ваш бюджет меньше, к сожалению, мы не сможем взять проект.\n"
            "Хотите начать заново? Напишите /start"
        )
        await state.clear()
        return

    # Если бюджет нормальный — продолжаем
    await state.update_data(budget=message.text)
    await message.answer("Отлично! Последний шаг.\nУкажите ваши контакты (имя + Telegram или телефон):")
    await state.set_state(ProjectForm.waiting_contact)

# ===================== Финальная отправка =====================
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
    await message.answer("✅ Заявка отправлена! Мы свяжемся с вами в ближайшее время.", reply_markup=get_main_menu())
    await state.clear()

# ===================== Остальные разделы =====================
@dp.callback_query(F.data.in_(["services", "prices", "about", "process", "contact"]))
async def show_sections(call: types.CallbackQuery):
    texts = {
        "services": "🛠 <b>Услуги</b>\n\n• Премиальные сайты\n• Telegram-боты\n• Мобильные приложения\n• Брендинг",
        "prices": "💰 <b>Цены</b>\n\nПодробные цены смотрите при оформлении заявки",
        "about": "👑 <b>О нас</b>\n\nLuce. — студия цифровой роскоши",
        "process": "⚡ <b>Процесс</b>\n\n1. Брифинг\n2. Дизайн\n3. Разработка\n4. Тестирование\n5. Запуск",
        "contact": "📞 <b>Связаться</b>\n\nНапишите: mollyhuetonn@gmail.com"
    }
    await call.message.edit_text(texts[call.data], reply_markup=get_main_menu())

# ===================== Запуск =====================
async def main():
    print("🚀 Бот Luce. успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
