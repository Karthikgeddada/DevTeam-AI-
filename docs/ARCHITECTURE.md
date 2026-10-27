# DevTeam AI — Architecture

## Overview

DevTeam AI is an incremental, persistent AI coding workspace built on Streamlit. It lets users describe changes in natural language, generates structured implementation plans, produces per-task file diffs, and applies changes only after human review. All state is persisted to SQLite, enabling session resumption and crash recovery.

The system is organized into seven layers, each with a single responsibility:

```
UI Layer (Streamlit)
  workspace, project_explorer, code_editor, chat, task_panel, diff_viewer

Workflow / Orchestration
  graph.py (IncrementalWorkflow), task_state.py

Agents
  planner_agent, coder_agent, context_agent

Services
  project, task, diff, checkpoint, usage, validation, persistence (ServiceContainer)

Providers (LLM Abstraction)
  base, errors, retry, registry
  gemini, deepseek, qwen, ollama

Execution & Validation
  static_validator, isolated_executor

Storage & Security
  repository (ABC), sqlite_repository
  path_validator, audit
```

---

## Layer 1: Storage & Security

### Storage (`storage/`)

The persistence layer is built on the **Repository pattern** — an abstract `Repository` interface (`storage/repository.py`) defines all data operations, and `SQLiteRepository` (`storage/sqlite_repository.py`) provides the concrete implementation.

**Data models:**

| Model | Purpose |
|---|---|
| `ProjectRecord` | Project metadata (id, name, description, language, status) |
| `FileVersion` | Versioned file content with hash and created_by tracking |
| `TaskRecord` | A single task in an implementation plan with state, dependencies, and acceptance criteria |
| `DiffRecord` | A proposed or applied file change with base/proposed content and unified diff text |
| `CheckpointRecord` | Task recovery state snapshot |
| `UsageRecord` | Provider token usage and cost per request |
| `ConversationRecord` | Chat messages between user and assistant |

**Why SQLite?**

SQLite is chosen for portability on Streamlit Community Cloud, which provides a single container with no external database service. The database file (`data/devteam.db`) is a single file that survives container restarts. The `Repository` abstraction means a future migration to PostgreSQL or another database only requires implementing the interface.

### Security (`security/`)

Two modules provide defense-in-depth:

* **`path_validator.py`** — Prevents path traversal attacks (`../../../etc/passwd`), enforces blocked file extensions (`.exe`, `.sh`, `.dll`, etc.), limits file and archive sizes, and safely extracts ZIP archives with per-entry validation.
* **`audit.py`** — Structured JSON-lines audit logger that records file operations, provider calls, security events, and task transitions.

See [SECURITY.md](SECURITY.md) for the full security model.

---

## Layer 2: Execution & Validation

### Static Validation (`execution/static_validator.py`)

**Level A** validation runs without any code execution. It checks:

* Python syntax (via `ast.parse`)
* JSON validity
* HTML structure (doctype/html tags)
* Security patterns (hardcoded secrets, `eval()`, `exec()`, `shell=True`)
* Patch integrity (no duplicate file paths)
* Presence of `requirements.txt`

### Isolated Execution (`execution/isolated_executor.py`)

**Level B** validation (code execution) is **disabled by default**. Two implementations exist:

* `IsolatedExecutor` — Always reports unavailable. A placeholder for a future sandbox provider (Docker, E2B, etc.).
* `SubprocessExecutor` — Available only when `ENABLE_CODE_EXECUTION=true` is set in the environment. Restricted to an allowlist of commands (`python`, `pytest`, `pip`). Intended for local development only.

Arbitrary code is never executed in the Streamlit application process.

---

## Layer 3: Providers (LLM Abstraction)

The provider layer abstracts multiple LLM backends behind a uniform interface.

### Contract (`providers/base.py`)

Every provider implements `BaseProvider`:

* `is_available()` — Check if API key/endpoint is configured
* `get_models()` — Return list of supported models with metadata
* `generate(request)` — Non-streaming generation
* `stream_generate(request)` — Streaming generation (async iterator)
* `estimate_cost()` — Cost estimation based on token pricing

`GenerationRequest` and `GenerationResponse` are standardized dataclasses that all providers use, regardless of their native API format.

### Error Normalization (`providers/errors.py`)

Raw exceptions from provider SDKs are classified into `ProviderError` instances with an `ErrorCategory`:

| Category | Retryable | Example |
|---|---|---|
| `RATE_LIMIT` | Yes | HTTP 429 |
| `NETWORK_TIMEOUT` | Yes | Request timed out |
| `PROVIDER_OUTAGE` | Yes | HTTP 5xx, connection refused |
| `AUTH_ERROR` | No | HTTP 401, invalid API key |
| `QUOTA_EXHAUSTED` | No | Billing quota depleted |
| `INVALID_MODEL` | No | Model not found |
| `MALFORMED_RESPONSE` | No | JSON parse error |

### Retry Policy (`providers/retry.py`)

`RetryPolicy` implements bounded exponential backoff with jitter:

* Honors `Retry-After` headers when present
* Only retries `RATE_LIMIT`, `NETWORK_TIMEOUT`, and `PROVIDER_OUTAGE` categories
* Non-retryable errors (auth, quota, invalid model) are raised immediately
* Default: 3 retries, 1s base delay, 30s max delay, 25% jitter

### Registry (`providers/registry.py`)

`ProviderRegistry` is a singleton that:

* Registers all known providers at startup (safe — missing deps are skipped)
* Maintains a fallback chain: `gemini -> deepseek -> qwen -> ollama`
* Provides the first available provider as default

### Provider Adapters

| Provider | Module | API |
|---|---|---|
| Google Gemini | `gemini_provider.py` | `google-genai` SDK |
| DeepSeek | `deepseek_provider.py` | OpenAI-compatible API |
| Qwen/DashScope | `qwen_provider.py` | OpenAI-compatible API |
| Ollama (local) | `ollama_provider.py` | Local REST API, no key needed |

---

## Layer 4: Services

Services contain business logic and operate on the `Repository` interface. All services are wired together in a single `ServiceContainer` (`services/persistence.py`), which is a singleton initialized on first access.

| Service | Responsibility |
|---|---|
| `ProjectService` | Project CRUD, file save/get/delete, ZIP import/export, filesystem + DB sync |
| `TaskService` | Task creation, state transitions, dependency resolution, plan summaries |
| `DiffService` | Unified diff creation, accept/reject/revert with version conflict detection |
| `CheckpointService` | Task recovery snapshots for pause/resume and crash recovery |
| `UsageService` | Token usage accounting and cost aggregation |
| `ValidationService` | Orchestrates static validation and (disabled) isolated execution |

### ServiceContainer

```python
services = get_services()  # singleton
services.project_service.create_project("My App")
services.task_service.transition_task(task_id, "running")
services.diff_service.accept_diff_for_project(project_id, diff_id)
```

---

## Layer 5: Agents

Three agents form the incremental code generation pipeline:

### Planner Agent (`agents/planner_agent.py`)

Takes a user request + project context, asks the LLM to produce a structured JSON plan of 2-8 bounded tasks. Each task includes:

* Title and description
* Dependencies (0-based indices of prerequisite tasks)
* Acceptance criteria
* Files affected

### Context Agent (`agents/context_agent.py`)

Deterministic (non-LLM) agent that gathers relevant context for a task:

* Builds a text tree of the project structure
* Retrieves explicitly-affected files + keyword-matched files
* Assembles a context string for the coder agent

### Coder Agent (`agents/coder_agent.py`)

Generates targeted file changes for a single task. Returns a list of file dicts with `path`, `content`, and `action` (create/modify). Only includes files relevant to the current task - never regenerates the entire project.

---

## Layer 6: Workflow / Orchestration

### IncrementalWorkflow (`workflows/graph.py`)

The orchestrator ties agents, services, and providers together in a stateful, resumable workflow:

1. `plan_tasks()` — Planner Agent generates a task plan, saved via TaskService
2. `get_next_task()` — Returns the next pending task whose dependencies are satisfied
3. `execute_task()` — ContextAgent gathers context, CoderAgent generates file changes, DiffService creates proposed diffs. Task state: `pending -> running -> awaiting_review`
4. `accept_task_changes()` — Applies diffs, runs static validation, transitions to `completed` or `failed`
5. `reject_task_changes()` — Rejects all pending diffs for a task, transitions to `failed`
6. `pause_task()` / `resume_task()` — CheckpointService snapshots and restores state

Key properties:

* **Incremental** — One task at a time, not the entire project
* **Reviewable** — Every change is a diff that must be accepted or rejected
* **Resumable** — Paused/failed tasks can be resumed via checkpoints
* **Dependency-aware** — Tasks execute in dependency order

### Task State Machine (`workflows/task_state.py`)

States: `pending`, `running`, `awaiting_review`, `validating`, `completed`, `failed`, `paused`, `cancelled`

Valid transitions enforce that tasks cannot skip states (e.g., cannot go from `pending` directly to `completed`). Terminal states: `completed`, `cancelled`. Resumable states: `paused`, `failed`.

---

## Layer 7: UI (Streamlit)

The UI is a Streamlit application with a sidebar + two-column layout:

* **Sidebar** — Project Explorer (list, create, open, delete) + Settings (provider/model selection, usage metrics)
* **Left column** — Code Editor tab + Diff Review tab
* **Right column** — Chat panel tab + Task panel tab

| Module | Responsibility |
|---|---|
| `app.py` | Entry point, page config, session state init |
| `ui/workspace.py` | Main layout, provider/model selection, usage display |
| `ui/project_explorer.py` | Project list, create/open/delete, file tree |
| `ui/code_editor.py` | In-browser code editing with save |
| `ui/chat_panel.py` | Natural language request input, conversation history |
| `ui/task_panel.py` | Task list, plan summary, execute/accept/reject/pause/resume controls |
| `ui/diff_viewer.py` | Unified diff display with accept/reject per file |

---

## Configuration

All configuration is centralized in `config/settings.py` and reads from environment variables and Streamlit Secrets:

| Setting | Env Var | Default |
|---|---|---|
| DB path | `DEVTEAM_DB_PATH` | `data/devteam.db` |
| Projects dir | `DEVTEAM_PROJECTS_DIR` | `data/projects` |
| Audit log | `DEVTEAM_AUDIT_LOG` | `data/audit.log` |
| Default provider | `DEFAULT_PROVIDER` | `gemini` |
| Default model | `DEFAULT_MODEL` | `gemini-2.0-flash` |
| Max retries | `MAX_RETRIES` | `3` |
| Static validation | `ENABLE_STATIC_VALIDATION` | `true` |
| Code execution | `ENABLE_CODE_EXECUTION` | `false` |
| Max file size | `MAX_FILE_SIZE` | `10 MB` |
| Max archive size | (hardcoded) | `50 MB` |

---

## Data Flow Example

1. User opens a project and types: "Add a user login form"
2. `IncrementalWorkflow.plan_tasks()` calls the Planner Agent, which creates 3 tasks
3. User clicks Execute on Task 1
4. `execute_task()` calls ContextAgent to gather relevant files, then CoderAgent generates file changes, then DiffService creates proposed diffs
5. Task state transitions: `pending -> running -> awaiting_review`
6. User reviews diffs in the Diff Review tab
7. User clicks Accept, which triggers `accept_task_changes()`, applying diffs via DiffService, running static validation via ValidationService, and transitioning the task to `completed` or `failed`
8. User can pause at any step and resume later; checkpoints preserve state
9. Next task becomes available when dependencies are satisfied

---

## Testing

99 tests across 9 test files cover:

* Path security (traversal prevention, blocked extensions, ZIP safety)
* Diff creation and patch application
* Provider error classification (all 10 categories)
* Retry policy (retriable/non-retriable, exponential backoff, retry-after)
* Project persistence (checkpoint save/restore, restart recovery)
* Task state machine (valid/invalid transitions, terminal/resumable states)
* Static validation (syntax, JSON, security patterns, HTML)
* Archive extraction (safe ZIP handling)
* End-to-end integration

Run: `python -m pytest tests/ -v`