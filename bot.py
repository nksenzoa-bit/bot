import asyncio
import random
import string

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8857276674:AAGCC1F5vWY1nZkPz6KfVDH5aUsz98FLVio"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Генерация ключа доступа
ACCESS_KEY = "123456654321"

print(f"Ключ доступа: {123456654321}")

# Хранилище пользователей
users = {}

# Кнопки
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Снос")],
        [KeyboardButton(text="👤 Профиль")]
    ],
    resize_keyboard=True
)

back_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⬅ Назад")],
        [KeyboardButton(text="🏠 Главное меню")]
    ],
    resize_keyboard=True
)


class AuthState(StatesGroup):
    waiting_key = State()


class ActionState(StatesGroup):
    waiting_target = State()


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(AuthState.waiting_key)

    await message.answer(
        "🔐 Для доступа к боту введите ключ:"
    )


@dp.message(AuthState.waiting_key)
async def check_key(message: Message, state: FSMContext):
    if message.text != ACCESS_KEY:
        await message.answer("❌ Неверный ключ.")
        return

    user_id = message.from_user.id

    if user_id not in users:
        users[user_id] = {
            "actions": 0
        }

    await state.clear()

    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Вы успешно авторизованы.",
        reply_markup=main_menu
    )


@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user_id = message.from_user.id

    if user_id not in users:
        return

    stats = users[user_id]

    await message.answer(
        f"👤 Профиль\n\n"
        f"🆔 ID: {user_id}\n"
        f"📊 Выполнено задач: {stats['actions']}"
    )


@dp.message(F.text == "🚀 Снос")
async def action_menu(message: Message, state: FSMContext):
    await state.set_state(ActionState.waiting_target)

    await message.answer(
        "Введите username или ID:",
        reply_markup=back_menu
    )


@dp.message(F.text == "🏠 Главное меню")
async def home(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu
    )


@dp.message(F.text == "⬅ Назад")
async def back(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "↩ Возврат в меню",
        reply_markup=main_menu
    )


@dp.message(ActionState.waiting_target)
async def process_target(message: Message, state: FSMContext):
    target = message.text

    msg = await message.answer(
        f"🎯 Цель: {target}\n\n"
        f"⏳ Подготовка..."
    )

    total_time = 60  # секунд
    updates = 100    # шагов

    for percent in range(updates + 1):
        filled = percent // 5
        empty = 20 - filled

        bar = "🟩" * filled + "⬜" * empty

        await msg.edit_text(
            f"🎯 Цель: {target}\n\n"
            f"📊 Выполнение задачи\n\n"
            f"{bar}\n"
            f"{percent}%"
        )

        await asyncio.sleep(total_time / updates)

    users[message.from_user.id]["actions"] += 1

    await msg.edit_text(
        f"✅ Задача завершена\n\n"
        f"🎯 Цель: {target}\n"
        f"📈 Прогресс: 100%"
    )

    await state.clear()

    await message.answer(
        "Выберите действие:",
        reply_markup=main_menu
    )

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())