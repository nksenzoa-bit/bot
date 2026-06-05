import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")
ACCESS_KEY = "1233211"
ADMIN_ID = 6830012291

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ======================
# DB (RAM)
# ======================
users = {}
authorized = set()

# ======================
# STATES
# ======================
class AuthState(StatesGroup):
    wait_key = State()

class TaskState(StatesGroup):
    wait_input = State()

class AdminState(StatesGroup):
    wait_block = State()
    wait_unblock = State()

# ======================
# HELPERS
# ======================
def ensure(uid: int):
    if uid not in users:
        users[uid] = {"blocked": False, "actions": 0}

def is_blocked(uid: int):
    return users.get(uid, {}).get("blocked", False)

def is_auth(uid: int):
    return uid in authorized

def is_admin(uid: int):
    return uid == ADMIN_ID

# ======================
# KEYBOARDS
# ======================
user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚙️ Задача")],
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="💬 Поддержка")]
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚙️ Задача")],
        [KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="🚫 Заблокировать"), KeyboardButton(text="✅ Разблокировать")],
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="💬 Поддержка")]
    ],
    resize_keyboard=True
)

# ======================
# START + AUTH
# ======================
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    uid = message.from_user.id
    ensure(uid)

    if is_blocked(uid):
        return await message.answer("🚫 Вы заблокированы")

    if not is_auth(uid):
        await state.set_state(AuthState.wait_key)
        return await message.answer("🔐 Введите ключ доступа:")

    kb = admin_kb if is_admin(uid) else user_kb
    await message.answer("👋 Добро пожаловать!", reply_markup=kb)

# ======================
# KEY CHECK
# ======================
@dp.message(AuthState.wait_key)
async def check_key(message: Message, state: FSMContext):
    uid = message.from_user.id

    if message.text != ACCESS_KEY:
        return await message.answer("❌ Неверный ключ")

    authorized.add(uid)
    await state.clear()

    kb = admin_kb if is_admin(uid) else user_kb
    await message.answer("✅ Доступ открыт", reply_markup=kb)

# ======================
# PROFILE
# ======================
@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    uid = message.from_user.id

    if not is_auth(uid):
        return await message.answer("🔐 /start")

    ensure(uid)

    await message.answer(
        f"👤 Профиль\n"
        f"🆔 {uid}\n"
        f"📊 задач: {users[uid]['actions']}"
    )

# ======================
# SUPPORT
# ======================
@dp.message(F.text == "💬 Поддержка")
async def support(message: Message):
    await message.answer("💬 Поддержка: @ZloyAmazon")

# ======================
# LONG TASK (PROGRESS BAR)
# ======================
@dp.message(F.text == "⚙️ Задача")
async def task_start(message: Message, state: FSMContext):
    uid = message.from_user.id

    if not is_auth(uid):
        return await message.answer("🔐 /start")

    if is_blocked(uid):
        return await message.answer("🚫 Заблокирован")

    await state.set_state(TaskState.wait_input)
    await message.answer("✏️ Введите данные для обработки:")

@dp.message(TaskState.wait_input)
async def task_process(message: Message, state: FSMContext):
    uid = message.from_user.id
    data = message.text

    await state.clear()

    msg = await message.answer(f"⏳ Начало обработки\n📌 {data}\n0%")

    for i in range(1, 101):

        await asyncio.sleep(0.4)  # ~40 сек

        if i % 2 == 0:
            bar = "█" * (i // 5) + "░" * (20 - i // 5)

            await msg.edit_text(
                f"⏳ Обработка\n"
                f"📌 {data}\n"
                f"[{bar}] {i}%"
            )

    ensure(uid)
    users[uid]["actions"] += 1

    await msg.edit_text(f"✅ Готово\n📌 {data}\n100%")

# ======================
# USERS (ADMIN)
# ======================
@dp.message(F.text == "👥 Пользователи")
async def users_list(message: Message):
    if not is_admin(message.from_user.id):
        return

    text = "👥 Пользователи:\n\n"

    for uid, d in users.items():
        text += f"{uid} | {'🚫' if d['blocked'] else '✅'} | {d['actions']}\n"

    await message.answer(text)

# ======================
# BLOCK / UNBLOCK
# ======================
@dp.message(F.text == "🚫 Заблокировать")
async def block(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminState.wait_block)
    await message.answer("ID пользователя:")

@dp.message(AdminState.wait_block)
async def block_do(message: Message, state: FSMContext):
    uid = int(message.text)

    ensure(uid)
    users[uid]["blocked"] = True

    await state.clear()
    await message.answer("🚫 Заблокирован")

    try:
        await bot.send_message(uid, "🚫 Вас заблокировали")
    except:
        pass

@dp.message(F.text == "✅ Разблокировать")
async def unblock(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminState.wait_unblock)
    await message.answer("ID пользователя:")

@dp.message(AdminState.wait_unblock)
async def unblock_do(message: Message, state: FSMContext):
    uid = int(message.text)

    ensure(uid)
    users[uid]["blocked"] = False

    await state.clear()
    await message.answer("✅ Разблокирован")

    try:
        await bot.send_message(uid, "✅ Вас разблокировали")
    except:
        pass

# ======================
# RUN
# ======================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())