FROM node:22-bookworm-slim AS web
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
ENV EXPO_PUBLIC_API_URL=/
ENV CI=1
RUN npx expo export --platform web --output-dir dist

FROM python:3.13-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ /app/backend/
COPY frontend/app/ /app/frontend/app/
COPY README.md /app/README.md
COPY frontend/components/ /app/frontend/components/
COPY docs/ /app/docs/
COPY --from=web /app/frontend/dist /app/frontend/dist
RUN test -f /app/frontend/dist/index.html
RUN useradd --create-home citizen && chown -R citizen:citizen /app
USER citizen
EXPOSE 10000
CMD ["sh","-c","exec python -m uvicorn backend.src.publicacao:app --host 0.0.0.0 --port ${PORT:-10000}"]
