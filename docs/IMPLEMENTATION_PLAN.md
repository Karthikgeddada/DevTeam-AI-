# DevTeam AI - Implementation Plan

## Project Goal

Transform the original DevTeam-AI monolithic Streamlit app into a production-grade, incremental AI coding workspace with:

* Multi-provider LLM abstraction with fallback
* Durable persistence (SQLite) with file versioning
* Path-validated, audit-logged file operations
* Incremental, reviewable code generation (plan -> execute -> review -> accept/reject -> validate)
* Two-level validation (static + isolated execution)
* Crash recovery via checkpoints

---

## Phase 1: Foundation (Storage, Security, Providers)

### 1.1 Security Layer
* `security/path_validator.py` - Path traversal prevention, blocked extensions, safe ZIP extraction
* `security/audit.py` - Structured JSON-lines audit logger
* Tests: `test_path_security.py`, `test_archive_extraction.py`

### 1.2 Provider Abstraction
* `providers/base.py` - `BaseProvider` ABC, `GenerationRequest`, `GenerationResponse`, `ModelInfo`
* `providers/errors.py` - `ErrorCategory` enum (10 categories), `ProviderError`, `classify_error()`
* `providers/retry.py` - `RetryPolicy` with exponential backoff, jitter, retry-after support
* `providers/registry.py` - `ProviderRegistry` singleton, fallback chain, auto-registration
* Provider adapters: `gemini_provider.py`, `deepseek_provider.py`, `qwen_provider.py`, `ollama_provider.py`
* Tests: `test_provider_errors.py`, `test_retry_policy.py`

### 1.3 Storage Layer
* `storage/repository.py` - Abstract `Repository` interface + data models (`ProjectRecord`, `FileVersion`, `TaskRecord`, `DiffRecord`, `CheckpointRecord`, `UsageRecord`, `ConversationRecord`)
* `storage/sqlite_repository.py` - Full SQLite implementation with schema creation
* `config/settings.py` - Centralized configuration from env vars + Streamlit Secrets
* Tests: `test_project_persistence.py`

---

## Phase 2: Services & Validation

### 2.1 Service Layer
* `services/persistence.py` - `ServiceContainer` singleton wiring all services
* `services/project_service.py` - Project CRUD, file save/get/delete, ZIP import/export, audit events
* `services/task_service.py` - Task state transitions, dependency resolution, plan summaries
* `services/diff_service.py` - Unified diff creation, accept/reject/revert with version conflict detection
* `services/checkpoint_service.py` - Task recovery snapshots
* `services/usage_service.py` - Token accounting and cost aggregation
* `services/validation_service.py` - Orchestrates static + isolated validation
* Tests: `test_diff_patch.py`, `test_integration.py`

### 2.2 Execution & Validation
* `execution/base.py` - `ValidationResult`, `BaseValidator`, `BaseExecutor` ABCs
* `execution/static_validator.py` - Level A: syntax, JSON, HTML, security patterns, patch integrity
* `execution/isolated_executor.py` - Level B: disabled `IsolatedExecutor` + `SubprocessExecutor` (dev only)
* Tests: `test_static_validation.py`

---

## Phase 3: Incremental Agent Workflow

### 3.1 Agents
* `agents/planner_agent.py` - LLM-based planner producing structured JSON task plans
* `agents/context_agent.py` - Deterministic context gatherer (file tree, keyword matching)
* `agents/coder_agent.py` - Targeted per-task code generation

### 3.2 Workflow Orchestration
* `workflows/task_state.py` - `TaskState` enum (8 states), `VALID_TRANSITIONS`, `can_transition()`, `is_terminal()`, `can_resume()`
* `workflows/graph.py` - `IncrementalWorkflow` orchestrator: `plan_tasks()`, `execute_task()`, `accept_task_changes()`, `reject_task_changes()`, `pause_task()`, `resume_task()`
* Tests: `test_task_state.py`

---

## Phase 4: Streamlit UI

### 4.1 Entry Point
* `app.py` - Page config, session state initialization, workspace rendering

### 4.2 UI Modules
* `ui/workspace.py` - Main layout, sidebar settings, provider/model selection, usage metrics
* `ui/project_explorer.py` - Project list, create/open/delete, file tree
* `ui/code_editor.py` - In-browser code editing with save
* `ui/chat_panel.py` - Natural language request input, conversation history
* `ui/task_panel.py` - Task list, plan summary, execute/accept/reject/pause/resume controls
* `ui/diff_viewer.py` - Unified diff display with accept/reject per file

---

## Phase 5: Configuration & Deployment

* `.streamlit/config.toml` - Streamlit UI configuration
* `.streamlit/secrets.toml.example` - API key template
* `requirements.txt` - Python dependencies
* `.gitignore` - Excludes data/, secrets, __pycache__
* `docs/DEPLOYMENT.md` - Deployment guide for Streamlit Community Cloud and local development

---

## Phase 6: Documentation

* `docs/ARCHITECTURE.md` - Seven-layer architecture with data flow and testing
* `docs/IMPLEMENTATION_PLAN.md` - This file
* `docs/IMPLEMENTATION_STATUS.md` - Acceptance criteria checklist with test summary
* `docs/SECURITY.md` - Security model and threat mitigation
* `README.md` - Project overview and quick start

---

## Design Decisions

### Why SQLite?
Streamlit Community Cloud provides a single container with no external database. SQLite is a single file that survives container restarts. The `Repository` abstraction enables future migration to PostgreSQL.

### Why disabled code execution?
Arbitrary code execution in the Streamlit process is a critical security risk. No verified sandbox is available on Streamlit Community Cloud. The `IsolatedExecutor` stub preserves the interface for a future Docker/E2B integration.

### Why incremental generation?
The original app regenerated the entire project on each request. The incremental workflow generates only the files needed for a single bounded task, making changes reviewable and the process resumable.

### Why a task state machine?
A formal state machine prevents invalid transitions (e.g., accepting changes before they are reviewed), enables pause/resume, and makes the workflow auditable.

---

## Future Enhancements

* Real-time streaming token display in the UI
* Docker-based isolated execution sandbox
* PostgreSQL backend for multi-user deployment
* User authentication and project sharing
* Git integration for version control
* WebSocket-based live collaboration
* Code completion and inline suggestions