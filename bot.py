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
TOKEN = os.getenv("BOT_TOKEN")  # токен бота из переменной окружения
ACCESS_KEY = "123456654321"     # твой ключ доступа

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ======================
# USERS DB (в памяти)
# ======================
users = {}

# ======================
# ADMINS
# ======================
ADMINS = [6830012291]  # <-- вставь сюда свой Telegram ID

# ======================
# STATES
# ======================
class AuthState(StatesGroup):
    waiting_key = State()  # для авторизации или ввода ID в админке

class SnosState(StatesGroup):
    waiting_target = State()

class AdminState(StatesGroup):
    waiting_user_id = State()

# ======================
# MENUS
# ======================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Снос"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="💬 Поддержка")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="🔒 Заблокировать")],
        [KeyboardButton(text="🗑 Удалить"), KeyboardButton(text="♻️ Сброс действий")],
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

    if user_id in users and users[user_id].get("authorized"):
        menu = admin_menu if user_id in ADMINS else main_menu
        await message.answer("👋 Добро пожаловать!", reply_markup=menu)
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
        "snos_count": 0,
        "blocked": False
    }

    await state.clear()
    menu = admin_menu if user_id in ADMINS else main_menu
    await message.answer("✅ Доступ разрешён", reply_markup=menu)

# ======================
# PROFILE
# ======================
@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user_id = message.from_user.id
    data = users.get(user_id, {"snos_count": 0, "blocked": False})

    await message.answer(
        f"👤 Профиль:\n"
        f"🔢 Всего действий: {data['snos_count']}\n"
        f"🚫 Заблокирован: {'Да' if data.get('blocked') else 'Нет'}"
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

    if users.get(user_id, {}).get("blocked"):
        await message.answer("🚫 Вы заблокированы и не можете использовать бота.")
        return

    target = message.text
    await state.clear()

    msg = await message.answer("⏳ Начинаем процесс... 0%")

    for i in range(1, 101):
        await asyncio.sleep(0.6)
        await msg.edit_text(f"⏳ Выполнение... {i}%")

    users[user_id]["snos_count"] += 1
    await msg.edit_text(f"✅ Готово!\n🎯 Объект: {target}")

# ======================
# ADMIN: VIEW USERS
# ======================
@dp.message(F.text == "👥 Пользователи")
async def view_users(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return

    if not users:
        await message.answer("Нет зарегистрированных пользователей.")
        return

    text = "👥 Пользователи:\n"
    for uid, data in users.items():
        text += f"{uid} — Действий: {data['snos_count']} — {'Заблокирован' if data.get('blocked') else 'Активен'}\n"

    await message.answer(text)

# ======================
# ADMIN: BLOCK USER
# ======================
@dp.message(F.text == "🔒 Заблокировать")
async def block_user_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    await state.set_state(AdminState.waiting_user_id)
    await message.answer("Введите ID пользователя для блокировки:")

@dp.message(AdminState.waiting_user_id)
async def block_user(message: Message, state: FSMContext):
    admin_id = message.from_user.id
    if admin_id not in ADMINS:
        return

    try:
        target_id = int(message.text)
    except ValueError:
        await message.answer("❌ Некорректный ID")
        return

    if target_id in users:
        users[target_id]["blocked"] = True
        await message.answer(f"✅ Пользователь {target_id} заблокирован")
    else:
        await message.answer("❌ Пользователь не найден")

    await state.clear()

# ======================
# ADMIN: DELETE USER
# ======================
@dp.message(F.text == "🗑 Удалить")
async def delete_user_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    await state.set_state(AdminState.waiting_user_id)
    await message.answer("Введите ID пользователя для удаления:")

@dp.message(AdminState.waiting_user_id)
async def delete_user(message: Message, state: FSMContext):
    admin_id = message.from_user.id
    if admin_id not in ADMINS:
        return

    try:
        target_id = int(message.text)
    except ValueError:
        await message.answer("❌ Некорректный ID")
        return

    if target_id in users:
        del users[target_id]
        await message.answer(f"✅ Пользователь {target_id} удалён")
    else:
        await message.answer("❌ Пользователь не найден")

    await state.clear()

# ======================
# ADMIN: RESET USER ACTIONS
# ======================
@dp.message(F.text == "♻️ Сброс действий")
async def reset_user_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    await state.set_state(AdminState.waiting_user_id)
    await message.answer("Введите ID пользователя для сброса действий:")

@dp.message(AdminState.waiting_user_id)
async def reset_user_actions(message: Message, state: FSMContext):
    admin_id = message.from_user.id
    if admin_id not in ADMINS:
        return

    try:
        target_id = int(message.text)
    except ValueError:
        await message.answer("❌ Некорректный ID")
        return

    if target_id in users:
        users[target_id]["snos_count"] = 0
        await message.answer(f"✅ Действия пользователя {target_id} сброшены")
    else:
        await message.answer("❌ Пользователь не найден")

    await state.clear()

# ======================
# RUN
# ======================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())