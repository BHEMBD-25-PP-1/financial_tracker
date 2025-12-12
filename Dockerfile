FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Переменные окружения (без секретов)
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Создание скрипта запуска
RUN echo '#!/bin/bash\n\
set -e\n\
if [ -z "$DB_HOST" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ]; then\n\
  echo "Ошибка: Необходимо установить переменные окружения DB_HOST, DB_USER, DB_PASSWORD, DB_NAME"\n\
  exit 1\n\
fi\n\
echo "Ожидание подключения к базе данных..."\n\
until pg_isready -h ${DB_HOST} -p ${DB_PORT:-5432} -U ${DB_USER}; do\n\
  echo "База данных недоступна - ожидание..."\n\
  sleep 2\n\
done\n\
echo "База данных доступна. Запуск миграций..."\n\
alembic upgrade head\n\
echo "Миграции выполнены. Запуск приложения..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
