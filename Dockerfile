FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && install -d -o appuser -g appuser /home/appuser/.streamlit

COPY --chown=appuser:appuser \
    main.py \
    tools.py \
    utils.py \
    transaction_db.py \
    llm-config.yaml \
    labs-logo.png \
    /app/
COPY --chown=appuser:appuser config.toml /home/appuser/.streamlit/config.toml

RUN chown appuser:appuser /app

ENV HOME=/home/appuser
USER appuser

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
