import json
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, SITE_URL, CONTACT_EMAIL, ADMIN_IDS

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# ===================== ADMIN STORAGE =====================

ADMINS_FILE = Path(__file__).parent / "admins.json"


def load_admins() -> list[int]:
    """Load admin IDs from config + JSON file."""
    ids = list(ADMIN_IDS)
    if ADMINS_FILE.exists():
        try:
            with open(ADMINS_FILE, "r", encoding="utf-8") as f:
                ids.extend(json.load(f))
        except (json.JSONDecodeError, ValueError):
            pass
    return list(set(ids))


def save_admin(user_id: int) -> None:
    """Add user_id to admins.json if not already there."""
    admins = load_admins()
    if user_id not in admins:
        admins.append(user_id)
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins, f, indent=2)


def remove_admin(user_id: int) -> None:
    """Remove user_id from admins.json."""
    admins = load_admins()
    if user_id in admins:
        admins.remove(user_id)
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins, f, indent=2)


async def notify_admins(text: str) -> None:
    """Send message to all registered admins."""
    for admin_id in load_admins():
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logging.warning(f"Не удалось отправить админу {admin_id}: {e}")

# ===================== KEYBOARDS =====================

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Услуги", callback_data="services")],
        [InlineKeyboardButton(text="Как мы работаем", callback_data="process")],
        [InlineKeyboardButton(text="О нас", callback_data="about")],
        [InlineKeyboardButton(text="Связаться с нами", callback_data="contact")],
    ])

def services_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создание ботов", callback_data="srv_bots")],
        [InlineKeyboardButton(text="Разработка сайтов", callback_data="srv_sites")],
        [InlineKeyboardButton(text="Мобильные приложения", callback_data="srv_apps")],
        [InlineKeyboardButton(text="AI/ML решения", callback_data="srv_ai")],
        [InlineKeyboardButton(text="UX/UI Дизайн", callback_data="srv_design")],
        [InlineKeyboardButton(text="Консалтинг", callback_data="srv_consult")],
        [InlineKeyboardButton(text="Назад", callback_data="back")],
    ])

def back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back")],
    ])

def order_kb(service_name: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Заказать: {service_name}", callback_data=f"order:{service_name}")],
        [InlineKeyboardButton(text="Назад", callback_data="services")],
    ])

def process_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оставить заявку", callback_data="contact")],
        [InlineKeyboardButton(text="Назад", callback_data="back")],
    ])

# ===================== SERVICE DATA =====================

SERVICES = {
    "srv_bots": {
        "title": "Создание Telegram-ботов",
        "desc": (
            "Разрабатываем ботов любой сложности:\n\n"
            "Простые — уведомления, FAQ, визитки\n"
            "Средние — магазины, сервисные боты, опросы\n"
            "Сложные — AI-ассистенты, CRM-интеграции, платёжные системы\n\n"
            "Стоимость: от 15 000 до 300 000+ руб.\n"
            "Срок: от 3 до 30 дней"
        ),
    },
    "srv_sites": {
        "title": "Разработка сайтов",
        "desc": (
            "Создаём современные веб-решения:\n\n"
            "Лендинги и промо-страницы\n"
            "Многостраничные корпоративные сайты\n"
            "Интернет-магазины с CMS\n"
            "Веб-приложения и SaaS-платформы\n\n"
            "Стоимость: от 30 000 до 800 000+ руб.\n"
            "Срок: от 7 до 60 дней"
        ),
    },
    "srv_apps": {
        "title": "Мобильные приложения",
        "desc": (
            "Нативные и кроссплатформенные приложения:\n\n"
            "iOS (Swift) / Android (Kotlin)\n"
            "Flutter / React Native — обе платформы\n"
            "Прототипирование и дизайн интерфейсов\n"
            "Публикация в App Store и Google Play\n\n"
            "Стоимость: от 80 000 до 1 500 000+ руб.\n"
            "Срок: от 14 до 90 дней"
        ),
    },
    "srv_ai": {
        "title": "AI/ML решения",
        "desc": (
            "Интеллектуальные системы на базе AI:\n\n"
            "Чат-боты с AI-логикой (LLM, RAG)\n"
            "Рекомендательные системы\n"
            "Предиктивная аналитика\n"
            "Обработка изображений и текста\n\n"
            "Стоимость: от 50 000 до 500 000+ руб.\n"
            "Срок: от 14 до 60 дней"
        ),
    },
    "srv_design": {
        "title": "UX/UI Дизайн",
        "desc": (
            "Проектирование пользовательских интерфейсов:\n\n"
            "UX-исследования и CJM\n"
            "Прототипы в Figma\n"
            "Дизайн-системы\n"
            "Аудит существующих интерфейсов\n\n"
            "Стоимость: от 20 000 до 200 000 руб.\n"
            "Срок: от 5 до 30 дней"
        ),
    },
    "srv_consult": {
        "title": "IT-консалтинг",
        "desc": (
            "Стратегическая помощь и аудит:\n\n"
            "Аудит IT-инфраструктуры\n"
            "Выбор технологий и стека\n"
            "Оптимизация процессов\n"
            "Планирование масштабирования\n\n"
            "Стоимость: от 10 000 руб./час\n"
            "Формат: онлайн-встречи + отчёт"
        ),
    },
}

# ===================== FSM =====================

class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_contact = State()
    waiting_for_details = State()

class AdminState(StatesGroup):
    waiting_for_forward_id = State()

# ===================== HANDLERS =====================

@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    text = (
        "Добро пожаловать в <b>LUCED</b>!\n\n"
        "Мы создаём технологические решения:\n"
        "ботов, сайты, мобильные приложения и AI-системы\n\n"
        "Выберите интересующий раздел:"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")

@router.message(F.text == "/services")
@router.callback_query(F.data == "services")
async def show_services(call: types.CallbackQuery | types.Message):
    text = "Выберите интересующую услугу:"
    if isinstance(call, types.CallbackQuery):
        await call.message.edit_text(text, reply_markup=services_menu())
        await call.answer()
    else:
        await call.answer(text, reply_markup=services_menu())

@router.callback_query(F.data.startswith("srv_"))
async def show_service_detail(call: types.CallbackQuery):
    srv = SERVICES.get(call.data)
    if not srv:
        await call.answer()
        return
    text = f"<b>{srv['title']}</b>\n\n{srv['desc']}"
    await call.message.edit_text(text, reply_markup=order_kb(srv["title"]), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("order:"))
async def start_order(call: types.CallbackQuery, state: FSMContext):
    service = call.data.split(":", 1)[1]
    await state.update_data(service=service)
    text = (
        f"Отлично! Вы хотите заказать: <b>{service}</b>\n\n"
        "Давайте обсудим детали. Напишите, пожалуйста:\n\n"
        "1. Ваше имя или название компании\n"
        "2. Контакт для связи (телеграм / телефон / email)\n"
        "3. Краткое описание задачи\n\n"
        "Начнём с имени:"
    )
    await call.message.edit_text(text, reply_markup=back_button(), parse_mode="HTML")
    await call.answer()
    await state.set_state(OrderState.waiting_for_name)

@router.message(OrderState.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(
        f"Спасибо, <b>{message.text}</b>!\n\n"
        "Теперь укажите ваш контакт для связи\n"
        "(@username, телефон или email):",
        parse_mode="HTML"
    )
    await state.set_state(OrderState.waiting_for_contact)

@router.message(OrderState.waiting_for_contact)
async def get_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text.strip())
    await message.answer(
        "Отлично! Опишите кратко вашу задачу:\n"
        "что нужно сделать, какие есть пожелания,\n"
        "примерные сроки и бюджет."
    )
    await state.set_state(OrderState.waiting_for_details)

@router.message(OrderState.waiting_for_details)
async def get_details(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("service", "Не указана")
    name = data.get("name", "Не указано")
    contact = data.get("contact", "Не указан")
    details = message.text.strip()

    admin_msg = (
        f"Новая заявка!\n\n"
        f"Услуга: {service}\n"
        f"Имя: {name}\n"
        f"Контакт: {contact}\n"
        f"Описание: {details}"
    )

    user_msg = (
        f"Спасибо, <b>{name}</b>! Ваша заявка принята.\n\n"
        f"Услуга: {service}\n"
        f"Мы свяжемся с вами в ближайшее время.\n\n"
        f"Наш сайт: {SITE_URL}\n"
        f"Email: {CONTACT_EMAIL}"
    )

    await message.answer(user_msg, parse_mode="HTML")
    await state.clear()

    # Отправляем заявку всем админам
    await notify_admins(admin_msg)

@router.callback_query(F.data == "process")
async def show_process(call: types.CallbackQuery):
    text = (
        "<b>Как мы работаем</b>\n\n"
        "1. Анализ — изучаем бизнес, рынок и конкурентов\n\n"
        "2. Дизайн — создаём прототипы и макеты\n\n"
        "3. Разработка — пишем чистый код с тестами\n\n"
        "4. Запуск — деплой, мониторинг и поддержка\n\n"
        "Каждый этап сопровождается отчётами и согласованием."
    )
    await call.message.edit_text(text, reply_markup=process_kb(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "about")
async def show_about(call: types.CallbackQuery):
    text = (
        "<b>LUCED</b> — команда энтузиастов, которая верит в силу технологий.\n\n"
        "С 2019 года мы создаём решения, которые помогают бизнесу расти и развиваться.\n\n"
        "Наши ценности:\n"
        "Инновации — всегда на передовой\n"
        "Прозрачность — честные сроки и цены\n"
        "Качество — каждый проект проходит ревью\n"
        "Команда — сильные специалисты с общей целью\n\n"
        f"Сайт: {SITE_URL}"
    )
    await call.message.edit_text(text, reply_markup=back_button(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "contact")
async def show_contact(call: types.CallbackQuery):
    text = (
        "<b>Свяжитесь с нами</b>\n\n"
        f"Email: {CONTACT_EMAIL}\n"
        f"Сайт: {SITE_URL}\n\n"
        "Или оставьте заявку прямо здесь — выберите услугу в меню и нажмите «Заказать»."
    )
    await call.message.edit_text(text, reply_markup=back_button(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "back")
async def go_back(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "Главное меню:"
    await call.message.edit_text(text, reply_markup=main_menu())
    await call.answer()

# ===================== ADMIN COMMANDS =====================

@router.message(F.text == "/admin")
async def cmd_admin(message: types.Message):
    """Добавить себя как владельца бота."""
    user_id = message.from_user.id
    admins = load_admins()

    if user_id in admins:
        await message.answer("Вы уже зарегистрированы как владелец.")
        return

    save_admin(user_id)
    await message.answer(
        f"Вы зарегистрированы как владелец бота!\n"
        f"Ваш ID: <code>{user_id}</code>\n\n"
        f"Теперь все заявки будут приходить вам в личные сообщения.",
        parse_mode="HTML"
    )

    # Уведомить других админов
    other_admins = [a for a in admins if a != user_id]
    for admin_id in other_admins:
        try:
            await bot.send_message(
                admin_id,
                f"Новый владелец зарегистрирован: "
                f"{message.from_user.full_name} (ID: <code>{user_id}</code>)",
                parse_mode="HTML"
            )
        except Exception:
            pass

@router.message(F.text == "/admin_remove")
async def cmd_admin_remove(message: types.Message):
    """Удалить себя из списка владельцев."""
    user_id = message.from_user.id
    admins = load_admins()

    if user_id not in admins:
        await message.answer("Вы не зарегистрированы как владелец.")
        return

    remove_admin(user_id)
    await message.answer("Вы удалены из списка владельцев.")

@router.message(F.text == "/admins")
async def cmd_admins_list(message: types.Message):
    """Показать список владельцев."""
    admins = load_admins()
    if not admins:
        await message.answer("Владельцев пока нет. Отправьте /admin чтобы стать владельцем.")
        return

    text = "Владельцы бота:\n\n"
    for aid in admins:
        text += f"• <code>{aid}</code>\n"
    await message.answer(text, parse_mode="HTML")

# ===================== RUN =====================

async def main():
    admins = load_admins()
    logging.info(f"Запуск бота... Владельцы: {admins}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
