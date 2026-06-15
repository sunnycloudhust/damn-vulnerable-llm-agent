FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && useradd --create-home --shell /usr/sbin/nologin appuser \
    && install -d -o appuser -g appuser /home/appuser/.streamlit \
    && install -d -o appuser -g appuser /app/runtime

COPY --chmod=0444 \
    main.py \
    tools.py \
    utils.py \
    transaction_db.py \
    audit_log.py \
    data_privacy.py \
    rate_limiter.py \
    llm-config.yaml \
    labs-logo.png \
    /app/
COPY --chmod=0444 config.toml /home/appuser/.streamlit/config.toml

ENV HOME=/home/appuser
ENV TRANSACTION_DB_PATH=/app/runtime/transactions.db
ENV RATE_LIMIT_DB_PATH=/app/runtime/rate_limit.db
ENV AUDIT_LOG_PATH=/app/runtime/logs/audit.jsonl
USER appuser

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
