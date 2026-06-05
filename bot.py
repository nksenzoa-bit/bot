import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_KEY = os.getenv("ACCESS_KEY", "1234512")
ADMIN_ID = int(os.getenv("6830012291", "0"))

users = {}

def ensure_user(uid):
    if uid not in users:
        users[uid] = {"banned": False, "uses": 0}

def banned(uid):
    return users.get(uid, {}).get("banned", False)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Снос", callback_data="simulate")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Ban", callback_data="ban")],
        [InlineKeyboardButton("✅ Unban", callback_data="unban")],
        [InlineKeyboardButton("👥 Users", callback_data="users")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid)

    if banned(uid):
        await update.message.reply_text("⛔ Вы заблокированы")
        return

    await update.message.reply_text("🔑 Введите ключ доступа:")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid)

    if banned(uid):
        return

    text = update.message.text

    # ADMIN ACTION
    if uid == ADMIN_ID and context.user_data.get("admin_action"):
        action = context.user_data["admin_action"]

        try:
            target = int(text)
            ensure_user(target)

            if action == "ban":
                users[target]["banned"] = True
                await update.message.reply_text(f"🚫 {target} заблокирован")

            elif action == "unban":
                users[target]["banned"] = False
                await update.message.reply_text(f"✅ {target} разблокирован")

        except:
            await update.message.reply_text("❌ Ошибка ID")

        context.user_data["admin_action"] = None
        return

    # ACCESS
    if text == ACCESS_KEY:
        await update.message.reply_text("✅ Доступ получен", reply_markup=main_menu())
    else:
        await update.message.reply_text("❌ Неверный ключ")

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    ensure_user(uid)

    await q.answer()

    if banned(uid):
        await q.edit_message_text("⛔ Заблокирован")
        return

    data = q.data

    if data == "profile":
        await q.edit_message_text(
            f"👤 Профиль\n\n⚙ Использований: {users[uid]['uses']}",
            reply_markup=main_menu()
        )

    elif data == "simulate":
        users[uid]["uses"] += 1

        msg = await q.edit_message_text("⚙ Запуск...")
        for i in range(5):
            time.sleep(0.5)
            await msg.edit_text("⚙ Выполнение" + "." * (i+1))

        await msg.edit_text("✅ Готово (Снос)", reply_markup=main_menu())

    elif data in ["ban", "unban", "users"]:
        if uid != ADMIN_ID:
            await q.edit_message_text("⛔ Нет доступа")
            return

        if data == "users":
            await q.edit_message_text(
                "👥 Users:\n" + "\n".join(map(str, users.keys())),
                reply_markup=admin_menu()
            )

        else:
            context.user_data["admin_action"] = data
            await q.edit_message_text("Введите ID пользователя:")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()