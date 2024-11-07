#!/bin/sh
# migration.sh

# Создание новой ревизии
alembic revision --autogenerate -m "Initial tables"

# Применение миграций
alembic upgrade head

# Вставка данных
python /app/deploy/local/database_migration/insert_data.py