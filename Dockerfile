FROM node:18 AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json .
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends nginx

WORKDIR /app

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Копируем только pyproject.toml сначала
COPY backend/pyproject.toml /app/

# Генерируем lock файл и устанавливаем зависимости
RUN poetry config virtualenvs.create false && \
    poetry lock --no-update 2>/dev/null || poetry lock && \
    poetry install --no-interaction --no-ansi --only main --no-root

# Копируем исходный код
COPY backend/src /app/src

# Копируем фронтенд
COPY --from=frontend-builder /frontend/build /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["sh", "-c", "nginx -g 'daemon off;' & uvicorn src.main:app --host 0.0.0.0 --port 8000"]