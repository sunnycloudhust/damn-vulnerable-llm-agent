# Damn Vulnerable LLM Agent - DevSecOps Fix Branch

[![DevSecOps Pipeline](https://github.com/sunnycloudhust/damn-vulnerable-llm-agent/actions/workflows/devsecops.yml/badge.svg?branch=fix)](https://github.com/sunnycloudhust/damn-vulnerable-llm-agent/actions/workflows/devsecops.yml?query=branch%3Afix)

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

Current important dependency changes on `fix`:

```text
litellm: 1.83.7 -> 1.84.0
aiohttp: 3.13.5 -> 3.14.0
```

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

## Pipeline Stages

### Build

Installs Python dependencies and verifies that the main runtime libraries import
successfully.

### SAST

Runs two static analysis tools:

- Semgrep with Python, security audit, and OWASP Top 10 rules.
- SonarQube Cloud with the project quality gate enabled.

On `fix`, SonarQube is scoped to Python source files. Dockerfile checks are
handled by Semgrep.

### SCA

Runs Snyk against `requirements.txt`:

```sh
snyk test --severity-threshold=high --file=requirements.txt --package-manager=pip --command=python
```

The workflow installs dependencies first, runs `pip check`, then runs Snyk in
the same Python environment. This prevents Snyk from scanning stale or global
packages.

### DAST

Starts the Streamlit app and scans it with OWASP ZAP baseline scan.

ZAP is configured with:

```text
cmd_options: -a -I
```

This keeps warnings visible in the report, but warnings alone do not fail the
pipeline. Alerts classified as failures still fail the DAST job.

### Quality Gate

The summary quality gate fails the pipeline if any of these jobs fail:

- Semgrep
- SonarQube
- Snyk

DAST is also a required job in the workflow graph and can fail independently if
ZAP reports blocking issues.

## Security Fixes In This Branch

The `fix` branch includes these remediation changes:

- Upgraded `litellm` to a patched version.
- Upgraded `aiohttp` to a patched version.
- Removed the Snyk workflow behavior that rewrote `requirements.txt`.
- Runs Snyk in the configured Python environment.
- Runs the Docker container as a non-root user.
- Uses a newer pinned OWASP ZAP action commit.
- Prevents ZAP warning-only results from failing the pipeline.
- Disables automatic GitHub issue creation from ZAP.
- Avoids duplicate workflow runs for the same PR update.

## Manual Workflow Run

You can manually trigger the workflow from GitHub:

1. Open the repository on GitHub.
2. Go to `Actions`.
3. Select `DevSecOps Pipeline`.
4. Click `Run workflow`.
5. Select branch `fix`.

The latest verified pull request runs on `fix` passed all jobs:

- Build
- Semgrep
- SonarQube
- Snyk
- OWASP ZAP
- Quality Gate

## Educational Vulnerabilities

The app intentionally remains useful as a prompt injection lab. It demonstrates
agent risks such as:

- Prompt injection against tool-using agents.
- Tool misuse through manipulated user input.
- SQL injection in the transaction lookup path.

Do not deploy this application as a real banking or production chatbot.

## License

This project is released under the Apache 2.0 license.
