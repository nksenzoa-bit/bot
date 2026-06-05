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
from aiogram.filters import CommandStart

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6830012291  # <-- твой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ======================
# DATABASE
# ======================
users = {}

# ======================
# HELPERS
# ======================
def ensure_user(uid: int):
    if uid not in users:
        users[uid] = {"blocked": False, "actions": 0}

def blocked(uid: int):
    return users.get(uid, {}).get("blocked", False)

def admin(uid: int):
    return uid == ADMIN_ID

# ======================
# KEYBOARDS
# ======================
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="💬 Поддержка")],
        [KeyboardButton(text="📊 Действие")]
    ],
    resize_keyboard=True
)

# ======================
# START
# ======================
@dp.message(CommandStart())
async def start(message: Message):
    uid = message.from_user.id
    ensure_user(uid)

    if blocked(uid):
        return await message.answer("🚫 Вы заблокированы")

    await message.answer("👋 Добро пожаловать!", reply_markup=main_kb)

# ======================
# PROFILE
# ======================
@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    uid = message.from_user.id
    ensure_user(uid)

    if blocked(uid):
        return await message.answer("🚫 Вы заблокированы")

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
# ACTION
# ======================
@dp.message(F.text == "📊 Действие")
async def action(message: Message):
    uid = message.from_user.id
    ensure_user(uid)

    if blocked(uid):
        return await message.answer("🚫 Вы заблокированы")

    msg = await message.answer("⏳ Выполняется...")

    await asyncio.sleep(1)

    users[uid]["actions"] += 1

    await msg.edit_text("✅ Успешно выполнено")

# ======================
# USERS INLINE LIST
# ======================
def users_keyboard():
    kb = []

    for uid, data in users.items():
        status = "🚫" if data["blocked"] else "✅"

        kb.append([
            InlineKeyboardButton(
                text=f"{status} {uid}",
                callback_data=f"user:{uid}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=kb)

# ======================
# USERS MENU
# ======================
@dp.message(F.text == "👥 Пользователи")
async def users_list(message: Message):
    uid = message.from_user.id

    if not admin(uid):
        return

    ensure_user(uid)

    await message.answer("👥 Пользователи:", reply_markup=users_keyboard())

# ======================
# USER PANEL
# ======================
@dp.callback_query(F.data.startswith("user:"))
async def user_panel(callback: CallbackQuery):
    if not admin(callback.from_user.id):
        return

    uid = int(callback.data.split(":")[1])
    ensure_user(uid)

    data = users[uid]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"block:{uid}")],
        [InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"unblock:{uid}")]
    ])

    await callback.message.edit_text(
        f"👤 USER {uid}\n"
        f"📊 Actions: {data['actions']}\n"
        f"🚫 Blocked: {data['blocked']}",
        reply_markup=kb
    )

# ======================
# BLOCK
# ======================
@dp.callback_query(F.data.startswith("block:"))
async def block_user(callback: CallbackQuery):
    if not admin(callback.from_user.id):
        return

    uid = int(callback.data.split(":")[1])
    ensure_user(uid)

    users[uid]["blocked"] = True

    await callback.answer("Заблокирован")

    try:
        await bot.send_message(uid, "🚫 Вас заблокировал администратор")
    except:
        pass

# ======================
# UNBLOCK
# ======================
@dp.callback_query(F.data.startswith("unblock:"))
async def unblock_user(callback: CallbackQuery):
    if not admin(callback.from_user.id):
        return

    uid = int(callback.data.split(":")[1])
    ensure_user(uid)

    users[uid]["blocked"] = False

    await callback.answer("Разблокирован")

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