FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH="/app"

RUN apt-get update && apt-get install -y --no-install-recommends \
    make curl build-essential libpq-dev nano micro \
    && pip install --no-cache-dir mutagen poetry==1.7.1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*  # Удаляем кэш apt для уменьшения размера

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && poetry install --no-root --no-ansi

COPY . ./