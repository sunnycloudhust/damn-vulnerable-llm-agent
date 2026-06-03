FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-dotenv

COPY --chmod=400 requirements.txt main.py tools.py utils.py transaction_db.py llm-config.yaml labs-logo.png /app/
RUN pip3 install -r requirements.txt
## fix here ##
RUN useradd -m appuser && chown -R appuser /app && chmod -R 500 /app
USER appuser
COPY --chown=root:appuser --chmod=0440 config.toml /home/appuser/.streamlit/config.toml
###

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]