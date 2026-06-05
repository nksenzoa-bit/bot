import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6830012291  # <-- твой ID

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ======================
# DATABASE
# ======================
users = {}

def ensure(uid: int):
    if uid not in users:
        users[uid] = {"blocked": False, "actions": 0}

def is_blocked(uid: int):
    return users.get(uid, {}).get("blocked", False)

def is_admin(uid: int):
    return uid == ADMIN_ID

# ======================
# STATES
# ======================
class AdminState(StatesGroup):
    wait_user_id = State()

pending_action = {}

# ======================
# KEYBOARDS
# ======================
user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Снос")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💬 Поддержка")]
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚙️ Выбор действий"), KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="👤 Профиль")]
    ],
    resize_keyboard=True
)

# ======================
# START
# ======================
@dp.message(CommandStart())
async def start(message: Message):
    uid = message.from_user.id
    ensure(uid)

    if is_blocked(uid):
        return await message.answer("🚫 Вы заблокированы")

    kb = admin_kb if is_admin(uid) else user_kb
    await message.answer("👋 Меню", reply_markup=kb)

# ======================
# PROFILE
# ======================
@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    uid = message.from_user.id
    ensure(uid)

    if is_blocked(uid):
        return await message.answer("🚫 Заблокирован")

    await message.answer(
        f"👤 Профиль\n"
        f"ID: {uid}\n"
        f"Действий: {users[uid]['actions']}"
    )

# ======================
# SUPPORT
# ======================
@dp.message(F.text == "💬 Поддержка")
async def support(message: Message):
    await message.answer("💬 Поддержка: @ZloyAmazon")

# ======================
# SNOS
# ======================
@dp.message(F.text == "🛠 Снос")
async def snos(message: Message):
    uid = message.from_user.id
    ensure(uid)

    if is_blocked(uid):
        return await message.answer("🚫 Заблокирован")

    msg = await message.answer("⏳ Выполняется...")

    await asyncio.sleep(2)
    await msg.edit_text("⚙️ Обработка...")

    await asyncio.sleep(2)
    await msg.edit_text("🔍 Проверка...")

    await asyncio.sleep(2)

    users[uid]["actions"] += 1

    await msg.edit_text("✅ Успешно выполнено")

# ======================
# ADMIN MENU
# ======================
@dp.message(F.text == "⚙️ Выбор действий")
async def admin_actions(message: Message):
    if not is_admin(message.from_user.id):
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Заблокировать", callback_data="action:block")],
        [InlineKeyboardButton(text="✅ Разблокировать", callback_data="action:unblock")]
    ])

    await message.answer("Выберите действие, затем отправьте ID пользователя:", reply_markup=kb)

# ======================
# USERS LIST (ADMIN)
# ======================
@dp.message(F.text == "👥 Пользователи")
async def show_users(message: Message):
    uid = message.from_user.id

    if not is_admin(uid):
        return

    if not users:
        return await message.answer("Пользователей нет")

    text = "👥 Пользователи:\n\n"

    for user_id, data in users.items():
        status = "🚫" if data["blocked"] else "✅"
        text += f"{status} {user_id} | действий: {data['actions']}\n"

    await message.answer(text)

# ======================
# SELECT ACTION
# ======================
@dp.callback_query(F.data.startswith("action:"))
async def set_action(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    action = callback.data.split(":")[1]
    pending_action[callback.from_user.id] = action

    await callback.answer("Теперь отправь ID пользователя")

# ======================
# PROCESS USER ID
# ======================
@dp.message(F.text)
async def process_id(message: Message, state: FSMContext):
    uid = message.from_user.id

    if not is_admin(uid):
        return

    if uid not in pending_action:
        return

    try:
        target = int(message.text)
    except:
        return await message.answer("❌ Введите корректный ID")

    ensure(target)

    action = pending_action[uid]

    if action == "block":
        users[target]["blocked"] = True
        await message.answer("🚫 Заблокирован")

        try:
            await bot.send_message(target, "🚫 Вас заблокировали")
        except:
            pass

    elif action == "unblock":
        users[target]["blocked"] = False
        await message.answer("✅ Разблокирован")

        try:
            await bot.send_message(target, "✅ Вас разблокировали")
        except:
            pass

    pending_action.pop(uid, None)