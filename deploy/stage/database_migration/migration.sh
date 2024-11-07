#!/bin/sh
# migration.sh

set -e
# Переход в директорию /app
cd /app

mkdir -p migration/versions
# Создание новой ревизии
alembic revision --autogenerate -m "Initial tables"

# Применение миграций
alembic upgrade head

# Вставка данных
python /app/deploy/stage/database_migration/insert_data.py