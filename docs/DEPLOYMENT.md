# DevTeam AI - Deployment Guide

## Prerequisites

* Python 3.10 or higher
* At least one LLM API key (Gemini, DeepSeek, Qwen, or local Ollama)
* Git (for cloning the repository)

---

## Local Development

### 1. Clone and Install

```bash
git clone <repository-url>
cd DevTeam-AI-main
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the secrets template and add your API keys:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
# Google Gemini (primary provider)
GEMINI_API_KEY = "your-gemini-api-key"

# DeepSeek (optional fallback)
DEEPSEEK_API_KEY = "your-deepseek-api-key"

# Qwen/DashScope (optional)
QWEN_API_KEY = "your-qwen-api-key"
```

Alternatively, set environment variables:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

### 4. Run Tests

```bash
python -m pytest tests/ -v
```

### 5. Enable Code Execution (Optional, Dev Only)

```bash
export ENABLE_CODE_EXECUTION=true
```

This enables the `SubprocessExecutor` for running generated code locally. Restricted to `python`, `pytest`, and `pip` commands with a 30-second timeout. Do not enable in production.

---

## Streamlit Community Cloud Deployment

### 1. Push to GitHub

Push the repository to a public or private GitHub repo. Make sure `.streamlit/secrets.toml` is NOT committed (it is in `.gitignore`).

### 2. Create a New App

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your repository and branch
4. Set the main file path to `app.py`
5. Click "Deploy"

### 3. Configure Secrets

In the Streamlit Cloud dashboard:

1. Open the app settings (three dots menu)
2. Go to "Secrets"
3. Add your API keys:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
DEEPSEEK_API_KEY = "your-deepseek-api-key"
```

4. Save and restart the app

### 4. Verify Deployment

* The app should load with the workspace UI
* The sidebar should show your configured provider as "available"
* Create a test project and verify files persist after a page reload

---

## Ollama (Local LLM) Setup

Ollama allows running LLMs locally without API keys.

### 1. Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull a Model

```bash
ollama pull llama3:8b
```

### 3. Start the Ollama Server

```bash
ollama serve  # runs on http://localhost:11434
```

### 4. Configure DevTeam AI

In `.streamlit/secrets.toml`:

```toml
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3:8b"
```

Or set environment variables:

```bash
export OLLAMA_BASE_URL="http://localhost:11434/v1"
export OLLAMA_MODEL="llama3:8b"
```

---

## Configuration Reference

All settings can be configured via environment variables or Streamlit Secrets:

| Setting | Env Var | Default | Description |
|---|---|---|---|
| DB path | `DEVTEAM_DB_PATH` | `data/devteam.db` | SQLite database location |
| Projects dir | `DEVTEAM_PROJECTS_DIR` | `data/projects` | Project file storage |
| Audit log | `DEVTEAM_AUDIT_LOG` | `data/audit.log` | Audit log file |
| Default provider | `DEFAULT_PROVIDER` | `gemini` | Initial provider selection |
| Default model | `DEFAULT_MODEL` | `gemini-2.0-flash` | Initial model selection |
| Max retries | `MAX_RETRIES` | `3` | LLM retry attempts |
| Static validation | `ENABLE_STATIC_VALIDATION` | `true` | Enable Level A validation |
| Code execution | `ENABLE_CODE_EXECUTION` | `false` | Enable Level B (dev only) |
| Max file size | `MAX_FILE_SIZE` | `10485760` | 10 MB per file |
| Max project size | `MAX_PROJECT_SIZE` | `52428800` | 50 MB per archive |

---

## Data Persistence

* **SQLite database** (`data/devteam.db`) - Projects, files, tasks, diffs, checkpoints, usage, audit
* **Project files** (`data/projects/<uuid>/`) - Actual file trees for each project
* **Audit log** (`data/audit.log`) - JSON-lines audit trail

On Streamlit Community Cloud, the `data/` directory persists across app restarts. For long-term backup, export projects as ZIP archives using the project explorer.

---

## Troubleshooting

### No provider available

The app shows a warning that no LLM provider is configured. Ensure at least one API key is set in Streamlit Secrets or environment variables.

### Provider errors (rate limit, timeout)

The retry policy handles transient errors automatically (3 retries with exponential backoff). For persistent errors, check your API key validity and quota.

### Database locked

SQLite supports one writer at a time. If you see "database is locked" errors, ensure only one instance of the app is running. For multi-user deployment, migrate to PostgreSQL by implementing the `Repository` interface.

### Files not persisting

Ensure the `data/` directory is writable. On Streamlit Community Cloud, verify the app has persistent storage enabled.