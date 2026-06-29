# Damn Vulnerable LLM Agent - DevSecOps Fix Branch

[![DevSecOps Pipeline](https://github.com/sunnycloudhust/damn-vulnerable-llm-agent/actions/workflows/devsecops.yml/badge.svg?branch=fix)](https://github.com/sunnycloudhust/damn-vulnerable-llm-agent/actions/workflows/devsecops.yml?query=branch%3Afix)
[![Snyk Security](https://snyk.io/test/github/sunnycloudhust/damn-vulnerable-llm-agent/fix/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/sunnycloudhust/damn-vulnerable-llm-agent/fix?targetFile=requirements.txt)
![SonarQube Quality Gate](https://img.shields.io/badge/SonarQube-Quality%20Gate%20Passed-4E9BCD?logo=sonarqube&logoColor=white)

This repository contains a deliberately vulnerable LLM agent lab and a fixed
branch that demonstrates how to remediate dependency and CI/CD security issues.

The application is a Streamlit chatbot built with LangChain and LiteLLM. It is
intended for learning about prompt injection, insecure agent tooling, SCA, SAST,
DAST, and security quality gates.

## Branch Model

This repository uses two main branches for the exercise:

- `main`: vulnerable baseline. It intentionally keeps insecure dependency
  versions so scanners can detect issues.
- `fix`: remediation branch. It upgrades vulnerable libraries and fixes the
  DevSecOps workflow so the pull request can pass.

## Application Setup

Create and activate a Python virtual environment:

```sh
python3 -m venv env
source env/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create a `.env` file from one of the templates:

```sh
cp .env.openai.template .env
```

Edit `.env` and set the required model provider variables. The active model is
selected with `model_name`; available model names are defined in
`llm-config.yaml`.

Run the application:

```sh
python -m streamlit run main.py
```

The app starts on:

```text
http://localhost:8501
```

## Docker

Build the image:

```sh
docker build -t dvla .
```

Run the image:

```sh
docker run --env-file .env -p 8501:8501 dvla
```

Security note for `fix`: the container no longer runs the application as root.
The Dockerfile creates and uses a non-root `appuser`.

## DevSecOps Workflow

The workflow is defined in:

```text
.github/workflows/devsecops.yml
```

It runs on:

- `push` to `main` or `master`
- `pull_request` targeting `main` or `master`
- manual `workflow_dispatch`

The `fix` branch is not listed under `push` to avoid duplicate runs when a pull
request from `fix` to `main` is open. Updating the PR still triggers the
workflow through the `pull_request` `synchronize` event.

## License

This project is released under the Apache 2.0 license.
