FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
COPY backend/requirements.txt ./backend/
COPY bot/requirements.txt ./bot/
RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r bot/requirements.txt

# Копируем код
COPY . .

# Создаем папку для базы данных
RUN mkdir -p /app/backend

# Явно указываем порт
ENV PORT=8000

# Запускаем API и бота
CMD ["sh", "-c", "cd /app/backend && uvicorn app:app --host 0.0.0.0 --port 8000 & cd /app/bot && python bot.py"]
