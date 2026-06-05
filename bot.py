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
ADMIN_ID = 6830012291  # <-- твой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ======================
# DATABASE (RAM)
# ======================
users = {}

# ======================
# STATES
# ======================
class AdminStates(StatesGroup):
    wait_block_id = State()
    wait_unblock_id = State()

# ======================
# KEYBOARDS
# ======================
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="💬 Поддержка")]
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="🚫 Заблокировать"), KeyboardButton(text="✅ Разблокировать")],
        [KeyboardButton(text="💬 Поддержка")]
    ],
    resize_keyboard=True
)

# ======================
# HELPERS
# ======================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def is_blocked(user_id: int) -> bool:
    return users.get(user_id, {}).get("blocked", False)

def ensure_user(user_id: int):
    if user_id not in users:
        users[user_id] = {
            "blocked": False,
            "actions": 0
        }

# ======================
# START
# ======================
@dp.message(CommandStart())
async def start(message: Message):
    uid = message.from_user.id

    ensure_user(uid)

    if is_blocked(uid):
        return await message.answer("🚫 Вы заблокированы")

    kb = admin_kb if is_admin(uid) else main_kb
    await message.answer("👋 Добро пожаловать!", reply_markup=kb)

# ======================
# PROFILE
# ======================
@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    uid = message.from_user.id

    if is_blocked(uid):
        return await message.answer("🚫 Доступ запрещён")

    ensure_user(uid)

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
# USERS LIST (ADMIN)
# ======================
@dp.message(F.text == "👥 Пользователи")
async def list_users(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        return

    text = "👥 Пользователи:\n\n"

    for user_id, data in users.items():
        text += f"{user_id} | blocked={data['blocked']} | actions={data['actions']}\n"

    await message.answer(text or "Пусто")

# ======================
# BLOCK USER
# ======================
@dp.message(F.text == "🚫 Заблокировать")
async def block_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.wait_block_id)
    await message.answer("Введите ID пользователя для блокировки:")

@dp.message(AdminStates.wait_block_id)
async def block_finish(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        target = int(message.text)
    except:
        return await message.answer("❌ Неверный ID")

    ensure_user(target)
    users[target]["blocked"] = True

    await state.clear()
    await message.answer("✅ Пользователь заблокирован")

    # уведомление пользователю
    try:
        await bot.send_message(target, "🚫 Вас заблокировал администратор")
    except:
        pass

# ======================
# UNBLOCK USER
# ======================
@dp.message(F.text == "✅ Разблокировать")
async def unblock_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.wait_unblock_id)
    await message.answer("Введите ID пользователя для разблокировки:")

@dp.message(AdminStates.wait_unblock_id)
async def unblock_finish(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        target = int(message.text)
    except:
        return await message.answer("❌ Неверный ID")

    ensure_user(target)
    users[target]["blocked"] = False

    await state.clear()
    await message.answer("✅ Пользователь разблокирован")

    try:
        await bot.send_message(target, "✅ Вас разблокировали")
    except:
        pass

# ======================
# SAFE ACTION EXAMPLE
# ======================
@dp.message(F.text == "📊 Действие")
async def action(message: Message):
    uid = message.from_user.id

    if is_blocked(uid):
        return await message.answer("🚫 Вы заблокированы")

    ensure_user(uid)

    msg = await message.answer("⏳ Выполняется...")

    await asyncio.sleep(1)

    users[uid]["actions"] += 1

    await msg.edit_text("✅ Успешно выполнено")

# ======================
# RUN
# ======================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())