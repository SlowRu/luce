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
    ids = list(ADMIN_IDS)
    if ADMINS_FILE.exists():
        try:
            with open(ADMINS_FILE, "r", encoding="utf-8") as f:
                ids.extend(json.load(f))
        except (json.JSONDecodeError, ValueError):
            pass
    return list(set(ids))


def save_admin(user_id: int) -> None:
    admins = load_admins()
    if user_id not in admins:
        admins.append(user_id)
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins, f, indent=2)


def remove_admin(user_id: int) -> None:
    admins = load_admins()
    if user_id in admins:
        admins.remove(user_id)
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins, f, indent=2)


async def notify_admins(text: str) -> None:
    for admin_id in load_admins():
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logging.warning(f"Не удалось отправить админу {admin_id}: {e}")

# ===================== SERVICE CATALOG =====================
# Каждая услуга имеет тарифы: id, название, цена, описание, срок

CATALOG = {
    "bots": {
        "category": "Telegram-боты",
        "emoji": "🤖",
        "items": [
            {
                "id": "bot_faq",
                "name": "Бот-визитка / FAQ",
                "price": 15_000,
                "desc": "Простой бот с информацией о компании, контактами и FAQ",
                "time": "3-5 дней",
            },
            {
                "id": "bot_notify",
                "name": "Бот уведомлений",
                "price": 25_000,
                "desc": "Автоматические уведомления, напоминания, оповещения о событиях",
                "time": "5-7 дней",
            },
            {
                "id": "bot_shop",
                "name": "Бот-магазин",
                "price": 60_000,
                "desc": "Каталог товаров, корзина, оплата через Telegram Stars / ЮKassa",
                "time": "10-14 дней",
            },
            {
                "id": "bot_support",
                "name": "Бот техподдержки",
                "price": 40_000,
                "desc": "Тикет-система, распределение заявок, чат с оператором",
                "time": "7-10 дней",
            },
            {
                "id": "bot_ai",
                "name": "AI-ассистент",
                "price": 120_000,
                "desc": "Умный бот на базе LLM с базой знаний, RAG и контекстом",
                "time": "14-21 дней",
            },
            {
                "id": "bot_crm",
                "name": "CRM-бот",
                "price": 200_000,
                "desc": "Управление клиентами, воронки, интеграция с Bitrix24/AmoCRM",
                "time": "21-30 дней",
            },
        ],
    },
    "sites": {
        "category": "Веб-сайты",
        "emoji": "🌐",
        "items": [
            {
                "id": "site_landing",
                "name": "Лендинг",
                "price": 30_000,
                "desc": "Одностраничный промо-сайт с анимациями и формой заявки",
                "time": "5-7 дней",
            },
            {
                "id": "site_corp",
                "name": "Корпоративный сайт",
                "price": 80_000,
                "desc": "Многостраничный сайт: главная, услуги, о нас, контакты, блог",
                "time": "14-21 дней",
            },
            {
                "id": "site_shop",
                "name": "Интернет-магазин",
                "price": 150_000,
                "desc": "Каталог, корзина, оплата, личный кабинет, админ-панель",
                "time": "21-35 дней",
            },
            {
                "id": "site_saas",
                "name": "Веб-приложение / SaaS",
                "price": 300_000,
                "desc": "Сложный веб-сервис с авторизацией, дашбордами, API",
                "time": "30-60 дней",
            },
            {
                "id": "site_seo",
                "name": "SEO-оптимизация сайта",
                "price": 25_000,
                "desc": "Аудит, оптимизация скорости, мета-теги, структурированные данные",
                "time": "5-10 дней",
            },
        ],
    },
    "apps": {
        "category": "Мобильные приложения",
        "emoji": "📱",
        "items": [
            {
                "id": "app_flutter",
                "name": "Кроссплатформенное (Flutter)",
                "price": 120_000,
                "desc": "Один код — iOS + Android. Быстро и экономично",
                "time": "21-35 дней",
            },
            {
                "id": "app_ios",
                "name": "Нативное iOS",
                "price": 200_000,
                "desc": "Swift, SwiftUI. Максимальная производительность для Apple",
                "time": "30-45 дней",
            },
            {
                "id": "app_android",
                "name": "Нативное Android",
                "price": 180_000,
                "desc": "Kotlin, Jetpack Compose. Полный доступ к возможностям Android",
                "time": "30-45 дней",
            },
            {
                "id": "app_mvp",
                "name": "MVP приложения",
                "price": 80_000,
                "desc": "Минимальная рабочая версия для теста гипотезы",
                "time": "14-21 дней",
            },
        ],
    },
    "ai": {
        "category": "AI / ML решения",
        "emoji": "🧠",
        "items": [
            {
                "id": "ai_chatbot",
                "name": "AI чат-бот для сайта",
                "price": 50_000,
                "desc": "Умный помощник на сайте с обучением на ваших данных",
                "time": "7-14 дней",
            },
            {
                "id": "ai_recs",
                "name": "Рекомендательная система",
                "price": 100_000,
                "desc": "Персональные рекомендации товаров, контента, услуг",
                "time": "14-28 дней",
            },
            {
                "id": "ai_analytics",
                "name": "Предиктивная аналитика",
                "price": 150_000,
                "desc": "Прогнозирование продаж, спроса, оттока клиентов",
                "time": "21-35 дней",
            },
            {
                "id": "ai_vision",
                "name": "Компьютерное зрение",
                "price": 200_000,
                "desc": "Распознавание объектов, лиц, документов, OCR",
                "time": "28-45 дней",
            },
        ],
    },
    "design": {
        "category": "UX/UI Дизайн",
        "emoji": "🎨",
        "items": [
            {
                "id": "design_landing",
                "name": "Дизайн лендинга",
                "price": 20_000,
                "desc": "Прототип + дизайн всех экранов в Figma",
                "time": "3-5 дней",
            },
            {
                "id": "design_multi",
                "name": "Дизайн многостраничника",
                "price": 50_000,
                "desc": "Полный дизайн 5-10 страниц с адаптивом",
                "time": "7-14 дней",
            },
            {
                "id": "design_system",
                "name": "Дизайн-система",
                "price": 80_000,
                "desc": "Компоненты, токены, гайдлайны для всей команды",
                "time": "14-21 дней",
            },
            {
                "id": "design_audit",
                "name": "Аудит интерфейса",
                "price": 25_000,
                "desc": "Анализ UX, рекомендации по улучшению, отчёт",
                "time": "3-7 дней",
            },
        ],
    },
    "devops": {
        "category": "DevOps / Cloud",
        "emoji": "☁️",
        "items": [
            {
                "id": "devops_setup",
                "name": "Настройка инфраструктуры",
                "price": 40_000,
                "desc": "Серверы, CI/CD, Docker, мониторинг",
                "time": "5-10 дней",
            },
            {
                "id": "devops_migrate",
                "name": "Миграция в облако",
                "price": 70_000,
                "desc": "Переезд на AWS/GCP/Azure без простоя",
                "time": "7-14 дней",
            },
            {
                "id": "devops_audit",
                "name": "Аудит инфраструктуры",
                "price": 30_000,
                "desc": "Оценка безопасности, производительности, стоимости",
                "time": "3-5 дней",
            },
        ],
    },
    "consult": {
        "category": "IT-консалтинг",
        "emoji": "💼",
        "items": [
            {
                "id": "consult_hour",
                "name": "Консультация (1 час)",
                "price": 10_000,
                "desc": "Онлайн-встреча, обсуждение задачи, рекомендации",
                "time": "1 час",
            },
            {
                "id": "consult_pack5",
                "name": "Пакет консультаций (5 часов)",
                "price": 40_000,
                "desc": "5 часов консультаций + письменный отчёт",
                "time": "гибко",
            },
            {
                "id": "consult_cto",
                "name": "Fractional CTO",
                "price": 150_000,
                "desc": "Технический директор на аутсорсе — стратегия, архитектура, контроль",
                "time": "от 1 месяца",
            },
        ],
    },
    "support": {
        "category": "Поддержка и сопровождение",
        "emoji": "🛡️",
        "items": [
            {
                "id": "support_basic",
                "name": "Базовая поддержка",
                "price": 15_000,
                "desc": "Мониторинг, бэкапы, обновления (1 проект/мес)",
                "time": "ежемесячно",
            },
            {
                "id": "support_pro",
                "name": "Про поддержка",
                "price": 35_000,
                "desc": "Базовая + мелкие доработки до 10 часов/мес",
                "time": "ежемесячно",
            },
            {
                "id": "support_enterprise",
                "name": "Enterprise",
                "price": 80_000,
                "desc": "Про + выделенный инженер, SLA, приоритетная поддержка",
                "time": "ежемесячно",
            },
        ],
    },
}

# Lookup: item_id -> (category_key, item)
ITEMS_BY_ID = {}
for cat_key, cat_data in CATALOG.items():
    for item in cat_data["items"]:
        ITEMS_BY_ID[item["id"]] = (cat_key, item)


def fmt_price(price: int) -> str:
    return f"{price:,}".replace(",", " ")

# ===================== KEYBOARDS =====================

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Каталог услуг", callback_data="services")],
        [InlineKeyboardButton(text="Корзина", callback_data="cart")],
        [InlineKeyboardButton(text="Как мы работаем", callback_data="process")],
        [InlineKeyboardButton(text="О нас", callback_data="about")],
        [InlineKeyboardButton(text="Контакты", callback_data="contact")],
    ])

def categories_kb():
    rows = []
    for cat_key, cat_data in CATALOG.items():
        rows.append([InlineKeyboardButton(
            text=f"{cat_data['emoji']} {cat_data['category']}",
            callback_data=f"cat:{cat_key}"
        )])
    rows.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def items_kb(cat_key: str):
    cat = CATALOG[cat_key]
    rows = []
    for item in cat["items"]:
        rows.append([InlineKeyboardButton(
            text=f"{item['name']} — {fmt_price(item['price'])} ₽",
            callback_data=f"item:{item['id']}"
        )])
    rows.append([InlineKeyboardButton(text="Назад", callback_data="services")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def item_detail_kb(item_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить в корзину", callback_data=f"add_cart:{item_id}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"cat:{ITEMS_BY_ID[item_id][0]}")],
    ])

def cart_kb(cart_items: list[dict]):
    rows = []
    for i, item in enumerate(cart_items):
        rows.append([InlineKeyboardButton(
            text=f"Удалить  {item['name']}",
            callback_data=f"remove_cart:{i}"
        )])
    rows.append([InlineKeyboardButton(text="Очистить корзину", callback_data="clear_cart")])
    rows.append([
        InlineKeyboardButton(text="Оформить заявку", callback_data="checkout"),
    ])
    rows.append([InlineKeyboardButton(text="Продолжить покупки", callback_data="services")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def back_button(cb="back"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data=cb)],
    ])

def process_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оставить заявку", callback_data="contact")],
        [InlineKeyboardButton(text="Назад", callback_data="back")],
    ])

# ===================== FSM =====================

class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_contact = State()
    waiting_for_details = State()

class AdminState(StatesGroup):
    waiting_for_admin_id = State()

# ===================== CART HELPERS =====================

def load_cart(user_id: int) -> list[dict]:
    cart_file = Path(__file__).parent / "carts" / f"{user_id}.json"
    if cart_file.exists():
        try:
            with open(cart_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            pass
    return []


def save_cart(user_id: int, cart: list[dict]) -> None:
    cart_dir = Path(__file__).parent / "carts"
    cart_dir.mkdir(exist_ok=True)
    cart_file = cart_dir / f"{user_id}.json"
    with open(cart_file, "w", encoding="utf-8") as f:
        json.dump(cart, f, indent=2, ensure_ascii=False)


def add_to_cart(user_id: int, item_id: str) -> bool:
    if item_id not in ITEMS_BY_ID:
        return False
    cat_key, item = ITEMS_BY_ID[item_id]
    cart = load_cart(user_id)
    cart.append({
        "id": item_id,
        "name": item["name"],
        "price": item["price"],
        "time": item["time"],
    })
    save_cart(user_id, cart)
    return True


def remove_from_cart(user_id: int, index: int) -> bool:
    cart = load_cart(user_id)
    if 0 <= index < len(cart):
        cart.pop(index)
        save_cart(user_id, cart)
        return True
    return False


def clear_cart(user_id: int) -> None:
    save_cart(user_id, [])


def cart_total(user_id: int) -> int:
    cart = load_cart(user_id)
    return sum(i["price"] for i in cart)


def cart_text(user_id: int) -> str:
    cart = load_cart(user_id)
    if not cart:
        return "Корзина пуста"
    lines = ["<b>Ваша корзина:</b>\n"]
    for i, item in enumerate(cart, 1):
        lines.append(f"{i}. {item['name']} — <b>{fmt_price(item['price'])} ₽</b>")
    lines.append(f"\n<b>Итого: {fmt_price(cart_total(user_id))} ₽</b>")
    return "\n".join(lines)

# ===================== HANDLERS =====================

@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    text = (
        "Добро пожаловать в <b>LUCED</b>!\n\n"
        "С 2025 года мы создаём технологические решения:\n"
        "ботов, сайты, мобильные приложения и AI-системы\n\n"
        "Выберите раздел:"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")

@router.message(F.text == "/cart")
@router.callback_query(F.data == "cart")
async def show_cart(call: types.CallbackQuery | types.Message):
    user_id = call.from_user.id
    text = cart_text(user_id)
    items = load_cart(user_id)
    kb = cart_kb(items) if items else back_button("services")
    if isinstance(call, types.CallbackQuery):
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await call.answer()
    else:
        await call.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "services")
async def show_services(call: types.CallbackQuery):
    text = "Выберите категорию услуг:"
    await call.message.edit_text(text, reply_markup=categories_kb())
    await call.answer()

@router.callback_query(F.data.startswith("cat:"))
async def show_category(call: types.CallbackQuery):
    cat_key = call.data.split(":", 1)[1]
    cat = CATALOG.get(cat_key)
    if not cat:
        await call.answer()
        return
    text = f"<b>{cat['emoji']} {cat['category']}</b>\n\nВыберите услугу:"
    await call.message.edit_text(text, reply_markup=items_kb(cat_key), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("item:"))
async def show_item(call: types.CallbackQuery):
    item_id = call.data.split(":", 1)[1]
    result = ITEMS_BY_ID.get(item_id)
    if not result:
        await call.answer()
        return
    cat_key, item = result
    text = (
        f"<b>{item['name']}</b>\n\n"
        f"{item['desc']}\n\n"
        f"Стоимость: <b>{fmt_price(item['price'])} ₽</b>\n"
        f"Срок: {item['time']}"
    )
    await call.message.edit_text(text, reply_markup=item_detail_kb(item_id), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("add_cart:"))
async def handle_add_cart(call: types.CallbackQuery):
    item_id = call.data.split(":", 1)[1]
    result = ITEMS_BY_ID.get(item_id)
    if not result:
        await call.answer()
        return
    cat_key, item = result
    add_to_cart(call.from_user.id, item_id)
    total = cart_total(call.from_user.id)
    await call.answer(f"Добавлено: {item['name']}", show_alert=False)
    text = (
        f"Добавлено: <b>{item['name']}</b> — {fmt_price(item['price'])} ₽\n\n"
        f"В корзине товаров на <b>{fmt_price(total)} ₽</b>"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть корзину", callback_data="cart")],
        [InlineKeyboardButton(text=f"Назад к {cat['category']}", callback_data=f"cat:{cat_key}")],
    ]), parse_mode="HTML")

@router.callback_query(F.data == "checkout")
async def start_checkout(call: types.CallbackQuery, state: FSMContext):
    text = cart_text(call.from_user.id)
    text += (
        "\n\nДля оформления заявки укажите:\n\n"
        "1. Ваше имя или название компании\n"
        "2. Контакт для связи (@username, телефон, email)\n"
        "3. Комментарии к заказу\n\n"
        "Начнём с имени:"
    )
    await call.message.edit_text(text, reply_markup=back_button("cart"), parse_mode="HTML")
    await call.answer()
    await state.set_state(OrderState.waiting_for_name)

@router.message(OrderState.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(
        f"Спасибо! Теперь укажите контакт для связи\n"
        f"(@username, телефон или email):",
        parse_mode="HTML"
    )
    await state.set_state(OrderState.waiting_for_contact)

@router.message(OrderState.waiting_for_contact)
async def get_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text.strip())
    await message.answer(
        "Есть комментарии или пожелания к заказу?\n"
        "Напишите что угодно или отправьте «—» если нет:"
    )
    await state.set_state(OrderState.waiting_for_details)

@router.message(OrderState.waiting_for_details)
async def get_details(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "Не указано")
    contact = data.get("contact", "Не указан")
    details = message.text.strip() if message.text.strip() != "—" else "Без комментариев"
    cart = load_cart(message.from_user.id)
    total = sum(i["price"] for i in cart)

    items_list = "\n".join(
        f"  • {i['name']} — {fmt_price(i['price'])} ₽ ({i['time']})"
        for i in cart
    )

    admin_msg = (
        f"Новый заказ!\n\n"
        f"Клиент: {name}\n"
        f"Контакт: {contact}\n\n"
        f"<b>Состав заказа:</b>\n{items_list}\n\n"
        f"<b>Итого: {fmt_price(total)} ₽</b>\n\n"
        f"Комментарий: {details}"
    )

    user_msg = (
        f"Спасибо, <b>{name}</b>! Ваш заказ принят.\n\n"
        f"Позиций: {len(cart)}\n"
        f"Сумма: <b>{fmt_price(total)} ₽</b>\n\n"
        f"Мы свяжемся с вами в ближайшее время для обсуждения деталей.\n\n"
        f"Сайт: {SITE_URL}\n"
        f"Email: {CONTACT_EMAIL}"
    )

    await message.answer(user_msg, parse_mode="HTML")
    clear_cart(message.from_user.id)
    await state.clear()
    await notify_admins(admin_msg)

@router.callback_query(F.data.startswith("remove_cart:"))
async def handle_remove_cart(call: types.CallbackQuery):
    index = int(call.data.split(":", 1)[1])
    remove_from_cart(call.from_user.id, index)
    items = load_cart(call.from_user.id)
    text = cart_text(call.from_user.id)
    kb = cart_kb(items) if items else back_button("services")
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer("Удалено из корзины")

@router.callback_query(F.data == "clear_cart")
async def handle_clear_cart(call: types.CallbackQuery):
    clear_cart(call.from_user.id)
    await call.message.edit_text("Корзина очищена", reply_markup=back_button("services"))
    await call.answer()

@router.callback_query(F.data == "process")
async def show_process(call: types.CallbackQuery):
    text = (
        "<b>Как мы работаем</b>\n\n"
        "1. <b>Анализ</b> — изучаем бизнес, рынок и конкурентов\n\n"
        "2. <b>Дизайн</b> — создаём прототипы и макеты\n\n"
        "3. <b>Разработка</b> — пишем чистый код с тестами\n\n"
        "4. <b>Запуск</b> — деплой, мониторинг и поддержка\n\n"
        "Каждый этап сопровождается отчётами и согласованием."
    )
    await call.message.edit_text(text, reply_markup=process_kb(), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "about")
async def show_about(call: types.CallbackQuery):
    text = (
        "<b>LUCED</b> — команда энтузиастов, которая верит в силу технологий.\n\n"
        "С 2025 года мы создаём решения, которые помогают бизнесу расти и развиваться.\n\n"
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
        "Или соберите корзину и оформите заявку прямо в боте."
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
    user_id = message.from_user.id
    admins = load_admins()
    if user_id in admins:
        await message.answer("Вы уже зарегистрированы как владелец.")
        return
    save_admin(user_id)
    await message.answer(
        f"Вы зарегистрированы как владелец бота!\n"
        f"Ваш ID: <code>{user_id}</code>\n\n"
        f"Теперь все заказы будут приходить вам.",
        parse_mode="HTML"
    )
    for admin_id in [a for a in admins if a != user_id]:
        try:
            await bot.send_message(
                admin_id,
                f"Новый владелец: {message.from_user.full_name} (ID: <code>{user_id}</code>)",
                parse_mode="HTML"
            )
        except Exception:
            pass

@router.message(F.text == "/admin_remove")
async def cmd_admin_remove(message: types.Message):
    user_id = message.from_user.id
    if user_id not in load_admins():
        await message.answer("Вы не зарегистрированы как владелец.")
        return
    remove_admin(user_id)
    await message.answer("Вы удалены из списка владельцев.")

@router.message(F.text == "/admins")
async def cmd_admins_list(message: types.Message):
    admins = load_admins()
    if not admins:
        await message.answer("Владельцев пока нет. Отправьте /admin чтобы стать владельцем.")
        return
    text = "Владельцы бота:\n\n" + "\n".join(f"• <code>{aid}</code>" for aid in admins)
    await message.answer(text, parse_mode="HTML")

# ===================== RUN =====================

async def main():
    admins = load_admins()
    logging.info(f"Запуск бота... Владельцы: {admins}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
