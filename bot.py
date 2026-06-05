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
ACCESS_KEY = "123456123"
ADMIN_ID = 6830012291  # твой ID

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ======================
# DATABASE
# ======================
users = {}
authorized = set()

# ======================
# STATES
# ======================
class AuthState(StatesGroup):
    wait_key = State()

class AdminStates(StatesGroup):
    wait_block_id = State()
    wait_unblock_id = State()

# ======================
# HELPERS
# ======================
def is_admin(uid: int):
    return uid == ADMIN_ID

def ensure(uid: int):
    if uid not in users:
        users[uid] = {"blocked": False, "actions": 0}

def is_blocked(uid: int):
    return users.get(uid, {}).get("blocked", False)

def is_auth(uid: int):
    return uid in authorized

# ======================
# KEYBOARDS
# ======================
user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Снос")],
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="💬 Поддержка")]
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Снос")],
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

    if is_blocked(uid):
        return await message.answer("🚫 Заблокирован")

    ensure(uid)

    await message.answer(
        f"👤 Профиль\n"
        f"🆔 ID: {uid}\n"
        f"📊 Действий: {users[uid]['actions']}"
    )

# ======================
# SUPPORT
# ======================
@dp.message(F.text == "💬 Поддержка")
async def support(message: Message):
    await message.answer("💬 Поддержка: @ZloyAmazon")

# ======================
# SNOS (USER + ADMIN)
# ======================
@dp.message(F.text == "🛠 Снос")
async def snos(message: Message):
    uid = message.from_user.id

    if not is_auth(uid):
        return await message.answer("🔐 /start")

    if is_blocked(uid):
        return await message.answer("🚫 Вы заблокированы")

    msg = await message.answer("⏳ Запуск...")

    await asyncio.sleep(1)
    await msg.edit_text("⚙️ Обработка...")

    await asyncio.sleep(1)
    await msg.edit_text("🔍 Проверка...")

    await asyncio.sleep(1)

    users[uid]["actions"] += 1

    await msg.edit_text("✅ Успешно выполнено")

# ======================
# USERS LIST (ADMIN)
# ======================
@dp.message(F.text == "👥 Пользователи")
async def users_list(message: Message):
    uid = message.from_user.id

    if not is_admin(uid):
        return

    text = "👥 Пользователи:\n\n"

    for user_id, data in users.items():
        status = "🚫" if data["blocked"] else "✅"
        text += f"{status} {user_id} | actions={data['actions']}\n"

    await message.answer(text)

# ======================
# BLOCK USER
# ======================
@dp.message(F.text == "🚫 Заблокировать")
async def block(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.wait_block_id)
    await message.answer("Введите ID пользователя:")

@dp.message(AdminStates.wait_block_id)
async def block_finish(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        target = int(message.text)
    except:
        return await message.answer("❌ Ошибка ID")

    ensure(target)
    users[target]["blocked"] = True

    await state.clear()
    await message.answer("🚫 Пользователь заблокирован")

    try:
        await bot.send_message(target, "🚫 Вас заблокировал администратор")
    except:
        pass

# ======================
# UNBLOCK USER
# ======================
@dp.message(F.text == "✅ Разблокировать")
async def unblock(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.wait_unblock_id)
    await message.answer("Введите ID пользователя:")

@dp.message(AdminStates.wait_unblock_id)
async def unblock_finish(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        target = int(message.text)
    except:
        return await message.answer("❌ Ошибка ID")

    ensure(target)
    users[target]["blocked"] = False

    await state.clear()
    await message.answer("✅ Пользователь разблокирован")

    try:
        await bot.send_message(target, "✅ Вас разблокировали")
    except:
        pass

# ======================
# RUN
# ======================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())