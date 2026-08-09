FROM python:3.11-slim

WORKDIR /app

# Копируем и устанавливаем зависимости для API и бота
COPY backend/requirements.txt ./backend/
COPY bot/requirements.txt ./bot/
RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r bot/requirements.txt

# Копируем весь код
COPY . .

# Запускаем и API, и бота в одном контейнере
CMD ["sh", "-c", "cd /app/backend && uvicorn app:app --host 0.0.0.0 --port $PORT & cd /app/bot && python bot.py"]
