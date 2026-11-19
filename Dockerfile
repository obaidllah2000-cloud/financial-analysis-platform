# 1) build the React interface
FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# 2) run the API, which also serves the built interface
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ backend/
COPY --from=web /web/dist frontend/dist
# writable data folder for any non-root runtime user (Hugging Face Spaces runs as uid 1000)
RUN mkdir -p /app/data && chmod 777 /app/data
ENV PORT=8000 FAP_DATA_DIR=/app/data
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
