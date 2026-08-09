import os
import sqlite3
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
MINI_APP_URL = os.getenv("MINI_APP_URL", "")

DB_PATH = "/opt/render/project/src/database.db"  # Render путь

def db():
    return sqlite3.connect(DB_PATH)

def is_creator(telegram_id: int) -> bool:
    conn = db()
    c = conn.cursor()
    c.execute("SELECT role FROM admins WHERE telegram_id = ? AND role = 'creator'", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("Открыть приложение", web_app=WebAppInfo(url=MINI_APP_URL))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Добро пожаловать в Project Evolution!\n\nНажмите кнопку ниже, чтобы открыть приложение.",
        reply_markup=reply_markup
    )

async def adm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_creator(update.effective_user.id):
        await update.message.reply_text("Доступ запрещен.")
        return
    
    keyboard = [[KeyboardButton("Админ-панель", web_app=WebAppInfo(url=f"{MINI_APP_URL}?admin=1"))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Админ-панель открыта.", reply_markup=reply_markup)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_creator(update.effective_user.id):
        await update.message.reply_text("Доступ запрещен.")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /admin @username")
        return
    
    username = context.args[0].replace('@', '')
    
    conn = db()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if not user:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
        conn.close()
        return
    
    try:
        c.execute("INSERT INTO admins (telegram_id, username, role) VALUES (?, ?, 'admin')",
                  (user[0], username))
        conn.commit()
        await update.message.reply_text(f"@{username} назначен администратором.")
    except:
        await update.message.reply_text(f"@{username} уже является администратором.")
    conn.close()

async def setadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_creator(update.effective_user.id):
        await update.message.reply_text("Доступ запрещен.")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /setadmin @username")
        return
    
    username = context.args[0].replace('@', '')
    
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE username = ? AND role != 'creator'", (username,))
    if c.rowcount > 0:
        await update.message.reply_text(f"@{username} снят с администратора.")
    else:
        await update.message.reply_text(f"@{username} не является администратором.")
    conn.commit()
    conn.close()

async def creator_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_creator(update.effective_user.id):
        await update.message.reply_text("Доступ запрещен.")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /creator @username")
        return
    
    username = context.args[0].replace('@', '')
    
    conn = db()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if not user:
        await update.message.reply_text(f"Пользователь @{username} не найден.")
        conn.close()
        return
    
    try:
        c.execute("INSERT OR REPLACE INTO admins (telegram_id, username, role) VALUES (?, ?, 'creator')",
                  (user[0], username))
        conn.commit()
        await update.message.reply_text(f"@{username} назначен создателем.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")
    conn.close()

async def admlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT username, role FROM admins ORDER BY role DESC")
    admins = c.fetchall()
    conn.close()
    
    if not admins:
        await update.message.reply_text("Список пуст.")
        return
    
    text = "Создатели и администраторы:\n\n"
    for username, role in admins:
        text += f"@{username} — {role}\n"
    
    await update.message.reply_text(text)

def main():
    conn = db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO admins (telegram_id, username, role) VALUES (?, ?, 'creator')",
                  (ADMIN_CHAT_ID, 'creator'))
        conn.commit()
    except:
        pass
    conn.close()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adm", adm_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("setadmin", setadmin_command))
    app.add_handler(CommandHandler("creator", creator_command))
    app.add_handler(CommandHandler("admlist", admlist_command))
    
    app.run_polling()

if __name__ == "__main__":
    main()
