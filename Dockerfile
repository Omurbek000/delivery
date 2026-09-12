# Онигири Delivery — multi-stage Dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
# Системные зависимости для Pillow/psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# Создаем не-root пользователя
RUN useradd -m appuser && mkdir -p /app/media /app/logs /app/static && chown -R appuser:appuser /app
# Копируем зависимости
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && rm -rf /wheels
# Копируем код
COPY --chown=appuser:appuser . .
# Собираем статику (если есть)
RUN python manage.py collectstatic --noinput || true
USER appuser
EXPOSE 8000
# Gunicorn: 3 воркера, таймаут 30с
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "30"]
