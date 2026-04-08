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
TOKEN = "8680466852:AAGlGmoqRCFOjJsXxk6s7wNWfWV45ylyu3I"   # ←←← ОБЯЗАТЕЛЬНО!
ADMIN_ID = 8207714217                        # ←←← ТВОЙ Telegram ID

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
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

# ===================== /start =====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "✺ <b>Luce.</b>\n\n"
        "Цифровой люкс нового поколения.\n\n"
        "Мы создаём премиальные цифровые продукты, которые выглядят дорого и работают безупречно.\n\n"
        "Выберите нужный раздел:"
    )
    await message.answer(text, reply_markup=get_main_menu())

# ===================== УСЛУГИ (расширенный раздел) =====================
@dp.callback_query(F.data == "services")
async def show_services(call: types.CallbackQuery):
    text = (
        "🛠 <b>Наши услуги</b>\n\n"
        "<b>Премиальные сайты</b>\n"
        "• Сайт-визитка / Лендинг\n"
        "• Корпоративный сайт\n"
        "• Интернет-магазин\n"
        "• Портфолио и персональные бренды\n"
        "• Эксклюзивные авторские сайты\n\n"
        
        "<b>Telegram-боты и мини-приложения</b>\n"
        "• Умные боты (заказы, консультации, продажи)\n"
        "• Боты для бизнеса и автоматизации\n"
        "• Игровые и развлекательные боты\n"
        "• Мини-приложения внутри Telegram\n\n"
        
        "<b>Мобильные приложения</b>\n"
        "• Приложения для iOS и Android\n"
        "• Кроссплатформенные решения\n"
        "• Приложения для бизнеса и клиентов\n\n"
        
        "<b>Дополнительно</b>\n"
        "• Полный брендинг и визуальная айдентика\n"
        "• 3D-дизайн и анимации\n"
        "• Интеграции и сложная автоматизация\n"
        "• Поддержка и развитие проектов"
    )
    await call.message.edit_text(text, reply_markup=get_main_menu())

# ===================== ЦЕНЫ (расширенный раздел) =====================
@dp.callback_query(F.data == "prices")
async def show_prices(call: types.CallbackQuery):
    text = (
        "💰 <b>Цены Luce.</b>\n\n"
        "<b>Telegram-боты</b>\n"
        "• Простой бот — <b>от 1 000 ₽</b>\n"
        "• Средний (с базой данных) — <b>от 2 000 ₽</b>\n"
        "• Сложный / магазинный — <b>от 3 000 ₽</b>\n\n"
        
        "<b>Сайты</b>\n"
        "• Сайт-визитка — <b>от 1 500 ₽</b>\n"
        "• Премиальный лендинг — <b>от 2 000 ₽</b>\n"
        "• Корпоративный / многостраничный — <b>от 4 000 ₽</b>\n"
        "• Интернет-магазин — <b>от 7 000 ₽</b>\n\n"
        
        "<b>Мобильные приложения</b>\n"
        "• Простое приложение — <b>от 3 000 ₽</b>\n"
        "• Полноценное приложение — <b>от 6 000 ₽</b>\n\n"
        
        "<b>Комплексные решения</b>\n"
        "• Брендинг + сайт — <b>от 5 000 ₽</b>\n"
        "• Бот + сайт + приложение — <b>от 8 000 ₽</b>\n\n"
        "💡 Цены указаны за базовый пакет. Точная стоимость зависит от ваших пожеланий."
    )
    await call.message.edit_text(text, reply_markup=get_main_menu())

# ===================== О НАС (расширенный раздел) =====================
@dp.callback_query(F.data == "about")
async def show_about(call: types.CallbackQuery):
    text = (
        "👑 <b>О нас — Luce.</b>\n\n"
        "Мы — независимая студия цифровой роскоши.\n\n"
        "В декабре 2025 года мы решили вернуть настоящее искусство в цифровой мир. "
        "За плечами нашей команды — годы работы в крупных агентствах, но мы выбрали путь свободы и эксклюзивности.\n\n"
        
        "За короткое время мы уже реализовали 9 эксклюзивных проектов для клиентов, которые ценят качество и индивидуальность.\n\n"
        
        "Наша философия проста: каждый продукт должен быть не просто «функциональным», "
        "а настоящим цифровым шедевром, которым можно гордиться."
    )
    await call.message.edit_text(text, reply_markup=get_main_menu())

# ===================== ПРОЦЕСС (расширенный раздел) =====================
@dp.callback_query(F.data == "process")
async def show_process(call: types.CallbackQuery):
    text = (
        "⚡ <b>Как мы работаем</b>\n\n"
        "<b>1. Брифинг и знакомство</b>\n"
        "Глубокое обсуждение ваших целей, задач и пожеланий.\n\n"
        
        "<b>2. Дизайн-концепция</b>\n"
        "Подготовка 2–3 уникальных вариантов дизайна.\n\n"
        
        "<b>3. Утверждение и доработки</b>\n"
        "Вносим правки до полного вашего удовлетворения.\n\n"
        
        "<b>4. Разработка</b>\n"
        "Программирование, интеграции, анимации.\n\n"
        
        "<b>5. Тестирование и полировка</b>\n"
        "Тщательная проверка на всех устройствах.\n\n"
        
        "<b>6. Запуск и поддержка</b>\n"
        "Передача проекта + дальнейшее развитие."
    )
    await call.message.edit_text(text, reply_markup=get_main_menu())

# ===================== СВЯЗАТЬСЯ =====================
@dp.callback_query(F.data == "contact")
async def show_contact(call: types.CallbackQuery):
    text = (
        "📞 <b>Связаться с нами</b>\n\n"
        "Самый удобный способ — нажать кнопку «Начать проект» ниже.\n\n"
        "Также можете написать нам на почту:\n"
        "<b>mollyhuetonn@gmail.com</b>\n\n"
        "Мы отвечаем очень оперативно."
    )
    await call.message.edit_text(text, reply_markup=get_main_menu())

# ===================== Заявка =====================
@dp.callback_query(F.data == "start_project")
async def start_project(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("💎 <b>Начать проект</b>\n\nОпишите вашу идею как можно подробнее. Что хотите создать?")
    await state.set_state(ProjectForm.waiting_description)

@dp.message(ProjectForm.waiting_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Отлично! Какой у вас примерный бюджет проекта?")
    await state.set_state(ProjectForm.waiting_budget)

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
        f"📝 Описание:\n{data['description']}\n\n"
        f"💰 Бюджет: {data['budget']}\n\n"
        f"📞 Контакты: {message.text}"
    )
    
    await bot.send_message(ADMIN_ID, final_text)
    await message.answer("✅ Спасибо! Ваша заявка получена.\nМы свяжемся с вами в ближайшее время.", reply_markup=get_main_menu())
    await state.clear()

# ===================== Запуск =====================
async def main():
    print("🚀 Бот Luce. успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
