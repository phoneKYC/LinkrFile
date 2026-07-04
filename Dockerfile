FROM python:3.12-slim

LABEL maintainer="IIDZII Dev"
LABEL description="linkr-bot — Telegram File-to-Link bot powered by GoFile"

WORKDIR /app

# Install Python dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Non-root user for security
RUN useradd -m -s /bin/bash botuser && chown -R botuser:botuser /app
USER botuser

HEALTHCHECK --interval=60s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/bot.py') else 1)"

CMD ["python", "bot.py"]