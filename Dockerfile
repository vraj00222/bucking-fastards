# Build the Next.js catalog
FROM node:20-slim AS webbuild
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
COPY data/ /app/data/
RUN npm run build

# Runtime: Node for the site + Python/ffmpeg for the sign-a-repo pipeline
FROM node:20-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv ffmpeg git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt
COPY pipeline/ pipeline/
COPY data/ data/
COPY --from=webbuild /app/web /app/web
ENV PYTHON=/venv/bin/python NODE_ENV=production PORT=8080
WORKDIR /app/web
EXPOSE 8080
CMD ["sh", "-c", "npx next start -p ${PORT}"]
