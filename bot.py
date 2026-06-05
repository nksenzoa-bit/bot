import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6830012291  # <-- твой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ======================
# DB
# ======================
users = {}

# ======================
# KEYBOARDS
# ======================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Профиль")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="🚫 Заблокировать"), KeyboardButton(text="✅ Разблокировать")]
    ],
    resize_keyboard=True
)

# ======================
# HELPER: BLOCK CHECK
# ======================
def is_blocked(user_id: int):
    return users.get(user_id, {}).get("blocked", False)

# ======================
# START
# ======================
@dp.message(F.text == "/start")
async def start(message: Message):
    uid = message.from_user.id

    if is_blocked(uid):
        await message.answer("🚫 Вы заблокированы и не можете использовать этого бота.")
        return

    if uid not in users:
        users[uid] = {"blocked": False, "actions": 0}

    await message.answer("👋 Привет!", reply_markup=main_menu)

# ======================
# PROFILE
# ======================
@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    uid = message.from_user.id

    if is_blocked(uid):
        await message.answer("🚫 Доступ запрещён.")
        return

    await message.answer(f"👤 Ваш профиль\nДействий: {users[uid]['actions']}")

# ======================
# ADMIN: USERS LIST
# ======================
@dp.message(F.text == "👥 Пользователи")
async def users_list(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = "👥 Пользователи:\n"
    for uid, data in users.items():
        text += f"{uid} | blocked={data['blocked']}\n"

    await message.answer(text)

# ======================
# BLOCK USER
# ======================
@dp.message(F.text == "🚫 Заблокировать")
async def block_prompt(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Введите ID пользователя для блокировки:")

@dp.message()
async def block_user(message: Message):
    uid = message.from_user.id

    if uid == ADMIN_ID and message.text.isdigit():
        target = int(message.text)

        if target in users:
            users[target]["blocked"] = True

            await message.answer("✅ Пользователь заблокирован")

            # уведомление пользователю
            try:
                await bot.send_message(target, "🚫 Вы были заблокированы администратором.")
            except:
                pass

# ======================
# UNBLOCK USER
# ======================
@dp.message(F.text == "✅ Разблокировать")
async def unblock_prompt(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Введите ID пользователя для разблокировки:")

@dp.message()
async def unblock_user(message: Message):
    uid = message.from_user.id

    if uid == ADMIN_ID and message.text.isdigit():
        target = int(message.text)

        if target in users:
            users[target]["blocked"] = False
            await message.answer("✅ Пользователь разблокирован")

            try:
                await bot.send_message(target, "✅ Вас разблокировали.")
            except:
                pass

# ======================
# EXAMPLE ACTION (safe)
# ======================
@dp.message(F.text == "📊 Действие")
async def action(message: Message):
    uid = message.from_user.id

    if is_blocked(uid):
        return

    users.setdefault(uid, {"blocked": False, "actions": 0})
    users[uid]["actions"] += 1

    msg = await message.answer("⏳ Выполняется...")

    await asyncio.sleep(2)

    await msg.edit_text("✅ Успешно выполнено")