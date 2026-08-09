import os
import sqlite3
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== ЖЕСТКО ЗАШИТЫЕ ДАННЫЕ =====
BOT_TOKEN = "8622607525:AAF1iK4in89aDzqtZpwxIGyjOdNXplAJnEg"
ADMIN_CHAT_ID = 7740890917  # БЕЗ КАВЫЧЕК!
MINI_APP_URL = "https://prevo-app.vercel.app"  # ПОМЕНЯЙ НА СВОЙ URL
# =================================

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "bot.db")

# Создаем папку для базы
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def db():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Создает таблицы при первом запуске"""
    conn = db()
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица администраторов
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT CHECK(role IN ('admin', 'creator'))
        )
    ''')
    
    # Добавляем создателя
    if ADMIN_CHAT_ID:
        c.execute('''
            INSERT OR REPLACE INTO admins (telegram_id, username, role)
            VALUES (?, ?, 'creator')
        ''', (ADMIN_CHAT_ID, 'creator'))
        print(f"👑 Создатель добавлен: {ADMIN_CHAT_ID}")
    
    conn.commit()
    conn.close()
    print(f"✅ База данных создана: {DB_PATH}")

def is_creator(telegram_id: int) -> bool:
    conn = db()
    c = conn.cursor()
    c.execute("SELECT role FROM admins WHERE telegram_id = ? AND role = 'creator'", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем пользователя
    try:
        conn = db()
        c = conn.cursor()
        c.execute('''
            INSERT OR IGNORE INTO users (telegram_id, username)
            VALUES (?, ?)
        ''', (update.effective_user.id, update.effective_user.username or "unknown"))
        conn.commit()
        conn.close()
    except:
        pass
    
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
    print("🚀 ЗАПУСК БОТА...")
    print(f"🔑 ADMIN_CHAT_ID = {ADMIN_CHAT_ID}")
    print(f"🤖 BOT_TOKEN = {BOT_TOKEN[:10]}...")
    print(f"🌐 MINI_APP_URL = {MINI_APP_URL}")
    
    # Инициализируем базу данных
    init_db()
    
    print("🤖 Бот запускается...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adm", adm_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("setadmin", setadmin_command))
    app.add_handler(CommandHandler("creator", creator_command))
    app.add_handler(CommandHandler("admlist", admlist_command))
    
    print("✅ Бот готов к работе! Жду команды...")
    app.run_polling()

if __name__ == "__main__":
    main()
