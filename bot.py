import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("8857276674:AAGCC1F5vWY1nZkPz6KfVDH5aUsz98FLVio")
ACCESS_KEY = "123456654321"  # твой ключ

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ======================
# USERS DB (в памяти)
# ======================
users = {}

# ======================
# STATES
# ======================
class AuthState(StatesGroup):
    waiting_key = State()

class SnosState(StatesGroup):
    waiting_target = State()

# ======================
# MENU
# ======================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Снос"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="💬 Поддержка")]
    ],
    resize_keyboard=True
)

# ======================
# START
# ======================
@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # уже авторизован
    if user_id in users and users[user_id].get("authorized"):
        await message.answer("👋 Добро пожаловать!", reply_markup=main_menu)
        return

    await state.set_state(AuthState.waiting_key)
    await message.answer("🔐 Введите ключ доступа:")

# ======================
# CHECK KEY
# ======================
@dp.message(AuthState.waiting_key)
async def check_key(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if message.text != ACCESS_KEY:
        await message.answer("❌ Неверный ключ")
        return

    users[user_id] = {
        "authorized": True,
        "snos_count": 0
    }

    await state.clear()
    await message.answer("✅ Доступ разрешён", reply_markup=main_menu)

# ======================
# PROFILE
# ======================
@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user_id = message.from_user.id
    data = users.get(user_id, {"snos_count": 0})

    await message.answer(
        f"👤 Профиль:\n"
        f"🔢 Всего действий: {data['snos_count']}"
    )

# ======================
# SUPPORT
# ======================
support_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать в поддержку", url="https://t.me/ZloyAmazon")]
    ]
)

@dp.message(F.text == "💬 Поддержка")
async def support(message: Message):
    await message.answer("💬 Поддержка:", reply_markup=support_kb)

# ======================
# SNOS START
# ======================
@dp.message(F.text == "🛠 Снос")
async def snos_start(message: Message, state: FSMContext):
    await state.set_state(SnosState.waiting_target)
    await message.answer("Введите username или ID:")

# ======================
# SNOS FAKE PROCESS
# ======================
@dp.message(SnosState.waiting_target)
async def snos_process(message: Message, state: FSMContext):
    user_id = message.from_user.id
    target = message.text

    await state.clear()

    msg = await message.answer("⏳ Начинаем процесс... 0%")

    for i in range(1, 101):
        await asyncio.sleep(0.6)  # ~1 минута
        await msg.edit_text(f"⏳ Выполнение... {i}%")

    users[user_id]["snos_count"] += 1

    await msg.edit_text(f"✅ Готово!\n🎯 Объект: {target}")

# ======================
# RUN
# ======================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())