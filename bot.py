diff --git a/bot.py b/bot.py
index d5238b3d0b2230b306b7a88cc8c8cfe4e09da0f0..27cfd8fb2d86c13737c79e26a2f1a680c9964ece 100644
--- a/bot.py
+++ b/bot.py
@@ -1,222 +1,377 @@
 import asyncio
 import logging
-from aiogram import Bot, Dispatcher, types, F
+import os
+import re
+from dataclasses import dataclass
+from typing import Dict, List
+
+from aiogram import Bot, Dispatcher, F, types
+from aiogram.client.default import DefaultBotProperties
+from aiogram.enums import ParseMode
 from aiogram.filters import Command
 from aiogram.fsm.context import FSMContext
 from aiogram.fsm.state import State, StatesGroup
-from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
-from aiogram.client.default import DefaultBotProperties
-from aiogram.enums import ParseMode
+from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
 
 # ===================== НАСТРОЙКИ =====================
-TOKEN = "8680466852:AAGlGmoqRCFOjJsXxk6s7wNWfWV45ylyu3I"
-ADMIN_ID = 8027714217
+TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
+ADMIN_ID = int(os.getenv("ADMIN_ID", "8027714217"))
+
+logging.basicConfig(level=logging.INFO)
+logger = logging.getLogger(__name__)
+
+if TOKEN == "PUT_YOUR_TOKEN_HERE":
+    logger.warning("BOT_TOKEN не задан. Укажите токен через переменную окружения BOT_TOKEN.")
 
 bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
 dp = Dispatcher()
 
-logging.basicConfig(level=logging.INFO)
 
-# ===================== Корзина (в памяти) =====================
-user_cart = {}  # {user_id: [list of services]}
+# ===================== ДАННЫЕ =====================
+@dataclass(frozen=True)
+class Service:
+    code: str
+    category: str
+    title: str
+    price: int
+
+
+SERVICES: Dict[str, Service] = {
+    "bot_simple": Service("bot_simple", "Боты", "🤖 Простой Telegram-бот", 1000),
+    "bot_medium": Service("bot_medium", "Боты", "🤖 Средний Telegram-бот", 2000),
+    "bot_hard": Service("bot_hard", "Боты", "🤖 Тяжёлый / магазинный бот", 3000),
+    "site_visitka": Service("site_visitka", "Сайты", "🌐 Сайт-визитка", 1000),
+    "site_landing": Service("site_landing", "Сайты", "🌐 Лендинг", 2000),
+    "site_corp": Service("site_corp", "Сайты", "🌐 Корпоративный сайт", 5000),
+    "site_shop": Service("site_shop", "Сайты", "🌐 Интернет-магазин", 8000),
+    "app_simple": Service("app_simple", "Приложения", "📱 Простое мобильное приложение", 2000),
+    "app_full": Service("app_full", "Приложения", "📱 Полноценное приложение (iOS + Android)", 8000),
+}
+
+CATEGORY_IMAGES = {
+    "Боты": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e",
+    "Сайты": "https://images.unsplash.com/photo-1461749280684-dccba630e2f6",
+    "Приложения": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c",
+    "main": "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
+}
+
+
+# ===================== Корзина и FSM =====================
+user_cart: Dict[int, List[str]] = {}
+
 
-# ===================== FSM =====================
 class ProjectForm(StatesGroup):
     waiting_contact = State()
+    waiting_comment = State()
+
+
+# ===================== УТИЛИТЫ =====================
+def format_price(value: int) -> str:
+    return f"{value:,}".replace(",", " ") + " ₽"
+
+
+def get_total(user_id: int) -> int:
+    return sum(SERVICES[item].price for item in user_cart.get(user_id, []))
+
+
+def add_to_cart(user_id: int, service_code: str) -> bool:
+    if user_id not in user_cart:
+        user_cart[user_id] = []
+    if service_code not in user_cart[user_id]:
+        user_cart[user_id].append(service_code)
+        return True
+    return False
+
+
+def remove_from_cart(user_id: int, service_code: str) -> bool:
+    if user_id in user_cart and service_code in user_cart[user_id]:
+        user_cart[user_id].remove(service_code)
+        return True
+    return False
+
+
+def clear_cart(user_id: int) -> None:
+    user_cart.pop(user_id, None)
+
+
+def cart_text(user_id: int) -> str:
+    items = user_cart.get(user_id, [])
+    if not items:
+        return "🛒 <b>Ваша корзина пуста</b>\n\nДобавляйте услуги из раздела «💰 Цены»."
+
+    lines = []
+    for idx, code in enumerate(items, start=1):
+        service = SERVICES[code]
+        lines.append(f"{idx}. {service.title} — <b>{format_price(service.price)}</b>")
+
+    return (
+        "🛒 <b>Ваша корзина</b>\n\n"
+        + "\n".join(lines)
+        + f"\n\n💵 <b>Итого:</b> {format_price(get_total(user_id))}"
+        + "\n\nНажмите «💎 Оформить заявку», чтобы продолжить."
+    )
+
 
-# ===================== Главное меню =====================
-def get_main_menu():
+def valid_contact(text: str) -> bool:
+    phone = re.search(r"\+?\d[\d\-\s()]{7,}", text)
+    telegram = "@" in text
+    return bool(phone or telegram)
+
+
+# ===================== КЛАВИАТУРЫ =====================
+def get_main_menu() -> InlineKeyboardMarkup:
     kb = [
-        [InlineKeyboardButton(text="🛠 Услуги", callback_data="services"),
-         InlineKeyboardButton(text="👑 О нас", callback_data="about")],
-        [InlineKeyboardButton(text="⚡ Процесс", callback_data="process"),
-         InlineKeyboardButton(text="💰 Цены", callback_data="prices")],
-        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
-         InlineKeyboardButton(text="💎 Оформить заявку", callback_data="start_project")],
-        [InlineKeyboardButton(text="📞 Связаться", callback_data="contact")]
+        [
+            InlineKeyboardButton(text="🛠 Услуги", callback_data="services"),
+            InlineKeyboardButton(text="👑 О нас", callback_data="about"),
+        ],
+        [
+            InlineKeyboardButton(text="⚡ Процесс", callback_data="process"),
+            InlineKeyboardButton(text="💰 Цены", callback_data="prices"),
+        ],
+        [
+            InlineKeyboardButton(text="🧩 Портфолио", callback_data="portfolio"),
+            InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
+        ],
+        [
+            InlineKeyboardButton(text="💎 Оформить заявку", callback_data="start_project"),
+            InlineKeyboardButton(text="📞 Связаться", callback_data="contact"),
+        ],
     ]
     return InlineKeyboardMarkup(inline_keyboard=kb)
 
-# ===================== Добавление в корзину =====================
-def add_to_cart(user_id, service):
-    if user_id not in user_cart:
-        user_cart[user_id] = []
-    if service not in user_cart[user_id]:
-        user_cart[user_id].append(service)
-
-# ===================== Показ корзины =====================
-def show_cart(user_id):
-    if user_id not in user_cart or not user_cart[user_id]:
-        return "🛒 Ваша корзина пуста.\n\nДобавляйте услуги из раздела «Цены»."
-    
-    items = "\n".join([f"• {item}" for item in user_cart[user_id]])
-    return f"🛒 <b>Ваша корзина</b>\n\n{items}\n\nНажмите «Оформить заявку», чтобы продолжить."
-
-# ===================== /start =====================
+
+def prices_menu() -> InlineKeyboardMarkup:
+    rows = []
+    for service in SERVICES.values():
+        rows.append(
+            [
+                InlineKeyboardButton(
+                    text=f"{service.title} — {format_price(service.price)}",
+                    callback_data=f"add_{service.code}",
+                )
+            ]
+        )
+    rows.append([InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="cart")])
+    rows.append([InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")])
+    return InlineKeyboardMarkup(inline_keyboard=rows)
+
+
+def cart_menu(user_id: int) -> InlineKeyboardMarkup:
+    rows = [[InlineKeyboardButton(text="💎 Оформить заявку", callback_data="start_project")]]
+
+    for code in user_cart.get(user_id, []):
+        rows.append(
+            [
+                InlineKeyboardButton(
+                    text=f"❌ Удалить: {SERVICES[code].title[:30]}",
+                    callback_data=f"remove_{code}",
+                )
+            ]
+        )
+
+    rows.extend(
+        [
+            [InlineKeyboardButton(text="🧹 Очистить корзину", callback_data="clear_cart")],
+            [InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")],
+        ]
+    )
+    return InlineKeyboardMarkup(inline_keyboard=rows)
+
+
+# ===================== СТАРТ =====================
 @dp.message(Command("start"))
 async def cmd_start(message: types.Message):
-    await message.answer(
-        "✺ <b>Luce.</b>\n\n"
-        "Цифровой люкс нового поколения.\n"
-        "Мы создаём премиальные продукты по очень приятным ценам.\n\n"
-        "Выберите раздел:",
-        reply_markup=get_main_menu()
+    await message.answer_photo(
+        CATEGORY_IMAGES["main"],
+        caption=(
+            "✺ <b>Luce.</b>\n\n"
+            "Цифровой люкс нового поколения.\n"
+            "Создаём премиальные сайты, ботов и приложения по приятным ценам.\n\n"
+            "Выберите раздел ниже 👇"
+        ),
+        reply_markup=get_main_menu(),
     )
 
-# ===================== ЦЕНЫ (максимально расширенный и живой раздел) =====================
+
+# ===================== РАЗДЕЛЫ =====================
+@dp.callback_query(F.data == "back_to_menu")
+async def back_to_menu(call: types.CallbackQuery):
+    await call.message.edit_caption(
+        caption="✺ <b>Luce.</b>\n\nВыберите раздел:",
+        reply_markup=get_main_menu(),
+    )
+
+
 @dp.callback_query(F.data == "prices")
 async def show_prices(call: types.CallbackQuery):
     text = (
-        "💰 <b>Цены Luce. — максимально доступный люкс</b>\n\n"
-        "Мы сделали цены очень привлекательными, чтобы вы могли позволить себе качественный цифровой продукт.\n\n"
-        
-        "<b>Telegram-боты</b>\n"
-        "• Простой бот — <b>1 000 ₽</b>\n"
-        "• Средний бот (с базой данных) — <b>2 000 ₽</b>\n"
-        "• Тяжёлый / магазинный бот — <b>3 000 ₽</b>\n\n"
-        
-        "<b>Сайты</b>\n"
-        "• Сайт-визитка — <b>1 000 ₽</b>\n"
-        "• Лендинг / продающий сайт — <b>2 000 ₽</b>\n"
-        "• Корпоративный сайт — <b>5 000 ₽</b>\n"
-        "• Интернет-магазин — <b>8 000 ₽</b>\n\n"
-        
-        "<b>Мобильные приложения</b>\n"
-        "• Простое приложение — <b>2 000 ₽</b>\n"
-        "• Полноценное приложение (iOS + Android) — <b>8 000 ₽</b>\n\n"
-        
-        "Нажмите на услугу ниже, чтобы добавить её в корзину 👇"
+        "💰 <b>Цены Luce.</b>\n\n"
+        "Выберите нужные услуги — они сразу добавятся в корзину.\n"
+        "Можно собрать полный пакет: бот + сайт + приложение."
     )
+    await call.message.edit_caption(caption=text, reply_markup=prices_menu())
+
 
-    kb = InlineKeyboardMarkup(inline_keyboard=[
-        [InlineKeyboardButton(text="🤖 Простой бот — 1 000 ₽", callback_data="add_bot_simple")],
-        [InlineKeyboardButton(text="🤖 Средний бот — 2 000 ₽", callback_data="add_bot_medium")],
-        [InlineKeyboardButton(text="🤖 Тяжёлый бот — 3 000 ₽", callback_data="add_bot_hard")],
-        [InlineKeyboardButton(text="🌐 Сайт-визитка — 1 000 ₽", callback_data="add_site_visitka")],
-        [InlineKeyboardButton(text="🌐 Лендинг — 2 000 ₽", callback_data="add_site_landing")],
-        [InlineKeyboardButton(text="🌐 Корпоративный сайт — 5 000 ₽", callback_data="add_site_corp")],
-        [InlineKeyboardButton(text="🌐 Интернет-магазин — 8 000 ₽", callback_data="add_site_shop")],
-        [InlineKeyboardButton(text="📱 Простое приложение — 2 000 ₽", callback_data="add_app_simple")],
-        [InlineKeyboardButton(text="📱 Полноценное приложение — 8 000 ₽", callback_data="add_app_full")],
-        [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="cart")]
-    ])
-
-    await call.message.edit_text(text, reply_markup=kb)
-
-# ===================== Добавление в корзину =====================
 @dp.callback_query(F.data.startswith("add_"))
 async def add_to_cart_handler(call: types.CallbackQuery):
-    user_id = call.from_user.id
-    service_map = {
-        "add_bot_simple": "🤖 Простой Telegram-бот — 1 000 ₽",
-        "add_bot_medium": "🤖 Средний Telegram-бот — 2 000 ₽",
-        "add_bot_hard": "🤖 Тяжёлый Telegram-бот — 3 000 ₽",
-        "add_site_visitka": "🌐 Сайт-визитка — 1 000 ₽",
-        "add_site_landing": "🌐 Лендинг — 2 000 ₽",
-        "add_site_corp": "🌐 Корпоративный сайт — 5 000 ₽",
-        "add_site_shop": "🌐 Интернет-магазин — 8 000 ₽",
-        "add_app_simple": "📱 Простое мобильное приложение — 2 000 ₽",
-        "add_app_full": "📱 Полноценное приложение — 8 000 ₽",
-    }
-    
-    service = service_map.get(call.data)
-    if service:
-        add_to_cart(user_id, service)
-        await call.answer("✅ Добавлено в корзину!", show_alert=True)
-    await call.message.edit_text("Добавлено в корзину! 👇", reply_markup=get_main_menu())
-
-# ===================== Корзина =====================
+    code = call.data.replace("add_", "", 1)
+    if code not in SERVICES:
+        await call.answer("Неизвестная услуга.", show_alert=True)
+        return
+
+    is_added = add_to_cart(call.from_user.id, code)
+    service = SERVICES[code]
+    if is_added:
+        await call.answer(f"✅ Добавлено: {service.title}", show_alert=True)
+    else:
+        await call.answer("ℹ️ Эта услуга уже в корзине", show_alert=True)
+
+
+@dp.callback_query(F.data.startswith("remove_"))
+async def remove_from_cart_handler(call: types.CallbackQuery):
+    code = call.data.replace("remove_", "", 1)
+    if remove_from_cart(call.from_user.id, code):
+        await call.answer("✅ Услуга удалена", show_alert=False)
+    else:
+        await call.answer("ℹ️ Услуга не найдена", show_alert=False)
+
+    await call.message.edit_caption(caption=cart_text(call.from_user.id), reply_markup=cart_menu(call.from_user.id))
+
+
+@dp.callback_query(F.data == "clear_cart")
+async def clear_cart_handler(call: types.CallbackQuery):
+    clear_cart(call.from_user.id)
+    await call.answer("🧹 Корзина очищена", show_alert=False)
+    await call.message.edit_caption(caption=cart_text(call.from_user.id), reply_markup=cart_menu(call.from_user.id))
+
+
 @dp.callback_query(F.data == "cart")
 async def show_cart_handler(call: types.CallbackQuery):
-    text = show_cart(call.from_user.id)
-    kb = InlineKeyboardMarkup(inline_keyboard=[
-        [InlineKeyboardButton(text="💎 Оформить заявку", callback_data="start_project")],
-        [InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")]
-    ])
-    await call.message.edit_text(text, reply_markup=kb)
+    await call.message.edit_caption(caption=cart_text(call.from_user.id), reply_markup=cart_menu(call.from_user.id))
 
-@dp.callback_query(F.data == "back_to_menu")
-async def back_to_menu(call: types.CallbackQuery):
-    await call.message.edit_text("✺ <b>Luce.</b>\n\nВыберите раздел:", reply_markup=get_main_menu())
 
-# ===================== Остальные разделы (живые) =====================
 @dp.callback_query(F.data == "services")
 async def show_services(call: types.CallbackQuery):
     text = (
         "🛠 <b>Наши услуги</b>\n\n"
-        "Мы создаём цифровые продукты, которые выглядят дорого, но стоят очень приятно.\n\n"
         "• Премиальные сайты и лендинги\n"
-        "• Умные Telegram-боты\n"
+        "• Telegram-боты любой сложности\n"
         "• Мобильные приложения\n"
-        "• Полный цифровой брендинг"
+        "• Упаковка продукта под ключ\n\n"
+        "Нажмите «💰 Цены», чтобы выбрать нужный пакет."
     )
-    await call.message.edit_text(text, reply_markup=get_main_menu())
+    await call.message.edit_caption(caption=text, reply_markup=get_main_menu())
+
 
 @dp.callback_query(F.data == "about")
 async def show_about(call: types.CallbackQuery):
     text = (
-        "👑 <b>О нас — Luce.</b>\n\n"
-        "Мы молодая, но очень амбициозная студия цифровой роскоши.\n"
-        "Наша цель — делать качественные продукты по максимально доступным ценам.\n\n"
-        "Уже сейчас мы помогаем людям и бизнесам получать красивые и рабочие решения."
+        "👑 <b>О студии Luce.</b>\n\n"
+        "Мы проектируем digital-продукты, которые выглядят дорого и работают быстро.\n"
+        "Делаем акцент на понятный интерфейс, стиль и результат для бизнеса."
     )
-    await call.message.edit_text(text, reply_markup=get_main_menu())
+    await call.message.edit_caption(caption=text, reply_markup=get_main_menu())
+
 
 @dp.callback_query(F.data == "process")
 async def show_process(call: types.CallbackQuery):
     text = (
-        "⚡ <b>Как мы работаем</b>\n\n"
-        "Всё максимально просто и прозрачно:\n"
-        "1. Вы описываете идею\n"
-        "2. Мы обсуждаем детали\n"
-        "3. Делаем вам крутой продукт\n"
-        "4. Вы получаете готовое решение"
+        "⚡ <b>Процесс работы</b>\n\n"
+        "1) Бриф и цели\n"
+        "2) Подбор стека и сметы\n"
+        "3) Дизайн и разработка\n"
+        "4) Тесты и запуск\n"
+        "5) Поддержка после релиза"
     )
-    await call.message.edit_text(text, reply_markup=get_main_menu())
+    await call.message.edit_caption(caption=text, reply_markup=get_main_menu())
+
+
+@dp.callback_query(F.data == "portfolio")
+async def show_portfolio(call: types.CallbackQuery):
+    text = (
+        "🧩 <b>Портфолио (примеры направлений)</b>\n\n"
+        "• Telegram-магазин с оплатой и CRM\n"
+        "• Лендинг для образовательного продукта\n"
+        "• Мобильное приложение для онлайн-записи\n\n"
+        "Хотите подобный проект — оформите заявку, и предложим архитектуру под вас."
+    )
+    await call.message.edit_caption(caption=text, reply_markup=get_main_menu())
+
 
 @dp.callback_query(F.data == "contact")
 async def show_contact(call: types.CallbackQuery):
-    text = "📞 <b>Связаться с нами</b>\n\nПросто нажмите «Оформить заявку» — это самый быстрый способ."
-    await call.message.edit_text(text, reply_markup=get_main_menu())
+    text = (
+        "📞 <b>Связь с командой</b>\n\n"
+        "Нажмите «💎 Оформить заявку» и отправьте ваш контакт: @username или телефон.\n"
+        "Мы ответим с планом работ и сроками."
+    )
+    await call.message.edit_caption(caption=text, reply_markup=get_main_menu())
+
 
-# ===================== Оформление заявки =====================
+# ===================== ОФОРМЛЕНИЕ ЗАЯВКИ =====================
 @dp.callback_query(F.data == "start_project")
 async def start_project(call: types.CallbackQuery, state: FSMContext):
-    cart_text = show_cart(call.from_user.id)
-    if "пуста" in cart_text:
-        await call.answer("Корзина пуста! Добавьте что-нибудь из раздела Цены.", show_alert=True)
+    if not user_cart.get(call.from_user.id):
+        await call.answer("Корзина пуста — сначала выберите услуги в разделе «Цены».", show_alert=True)
         return
-    
-    await call.message.edit_text(
-        f"{cart_text}\n\nНапишите ваши контакты (имя + Telegram или телефон), и мы сразу свяжемся с вами."
+
+    await call.message.answer(
+        f"{cart_text(call.from_user.id)}\n\n"
+        "✍️ Отправьте контакт для связи (телефон или @username)."
     )
     await state.set_state(ProjectForm.waiting_contact)
 
+
 @dp.message(ProjectForm.waiting_contact)
 async def process_contact(message: types.Message, state: FSMContext):
+    if not valid_contact(message.text or ""):
+        await message.answer("Похоже, контакт неполный. Отправьте телефон или @username.")
+        return
+
+    await state.update_data(contact=message.text)
+    await state.set_state(ProjectForm.waiting_comment)
+    await message.answer("Отлично! Добавьте комментарий к проекту (цель, сроки, пожелания).")
+
+
+@dp.message(ProjectForm.waiting_comment)
+async def process_comment(message: types.Message, state: FSMContext):
     user_id = message.from_user.id
-    cart = user_cart.get(user_id, [])
+    data = await state.get_data()
+    contact = data.get("contact", "не указан")
+    comment = message.text or "без комментария"
+    selected = user_cart.get(user_id, [])
+
+    items = "\n".join(
+        f"• {SERVICES[code].title} — {format_price(SERVICES[code].price)}" for code in selected
+    )
 
     final_text = (
-        f"📨 <b>НОВАЯ ЗАЯВКА С КОРЗИНОЙ</b>\n\n"
+        "📨 <b>НОВАЯ ЗАЯВКА LUCE</b>\n\n"
         f"👤 {message.from_user.first_name} (@{message.from_user.username or 'нет'})\n"
-        f"🆔 {message.from_user.id}\n\n"
-        f"🛒 Выбрано:\n" + "\n".join([f"• {item}" for item in cart]) + f"\n\n"
-        f"📞 Контакты: {message.text}"
+        f"🆔 {user_id}\n\n"
+        f"🛒 <b>Выбрано:</b>\n{items}\n\n"
+        f"💵 <b>Итого:</b> {format_price(get_total(user_id))}\n"
+        f"📞 <b>Контакт:</b> {contact}\n"
+        f"📝 <b>Комментарий:</b> {comment}"
     )
 
     await bot.send_message(ADMIN_ID, final_text)
-    await message.answer("✅ Заявка успешно отправлена!\nМы свяжемся с вами очень скоро.", reply_markup=get_main_menu())
-    
-    # Очищаем корзину после отправки
-    if user_id in user_cart:
-        del user_cart[user_id]
+    await message.answer(
+        "✅ Заявка отправлена!\n"
+        "Мы уже готовим план реализации и скоро свяжемся с вами.",
+        reply_markup=get_main_menu(),
+    )
+
+    clear_cart(user_id)
     await state.clear()
 
-# ===================== Запуск =====================
+
+# ===================== ЗАПУСК =====================
 async def main():
-    print("🚀 Бот Luce. успешно запущен!")
+    logger.info("🚀 Бот Luce запущен")
     await dp.start_polling(bot)
 
+
 if __name__ == "__main__":
     asyncio.run(main())
