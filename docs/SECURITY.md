# DevTeam AI - Security Model

## Overview

DevTeam AI is a web application that generates and modifies code files. This document describes the security architecture that protects against the primary threats: path traversal, arbitrary code execution, malicious archive extraction, and unauthenticated access.

---

## 1. Path Traversal Prevention

**Module:** `security/path_validator.py`

### `resolve_safe_path(project_root, relative_path)`

All file operations in the application go through `resolve_safe_path()`, which:

1. Rejects empty paths
2. Rejects absolute paths (starting with `/`)
3. Rejects Windows-style backslash traversal (`..\`)
4. Resolves the full path using `os.path.realpath()` (which collapses `..` and symlinks)
5. Verifies the resolved path starts with the project root + `os.sep`

This prevents attacks like `../../etc/passwd` or `../../../data/devteam.db`.

### Blocked File Extensions

The following extensions are blocked and cannot be created or extracted:

`.exe`, `.dll`, `.so`, `.dylib`, `.bin`, `.sh`, `.bat`, `.cmd`, `.ps1`, `.vbs`, `.app`, `.deb`, `.rpm`, `.msi`, `.dmg`, `.iso`

### File Size Limits

| Limit | Value |
|---|---|
| Max individual file size | 10 MB |
| Max archive size | 50 MB |
| Max archive entries | 5,000 |

These limits prevent denial-of-service through large file uploads or zip bombs.

---

## 2. Safe Archive Handling

**Function:** `safe_extract_zip(zip_data, project_root)`

ZIP archive extraction is the primary vector for path traversal and zip bombs. The safe extraction function:

1. Checks total archive size against `MAX_ARCHIVE_SIZE` (50 MB)
2. Checks entry count against `MAX_ARCHIVE_ENTRIES` (5,000)
3. For each entry: validates the path via `resolve_safe_path()` (prevents zip slip)
4. Checks each entry's file size against `MAX_FILE_SIZE` (10 MB)
5. Skips `__pycache__` entries and blocked extensions
6. Creates parent directories and writes the file only after all checks pass

If any check fails, the extraction is aborted with a `PathValidationError`.

---

## 3. No Arbitrary Code Execution

**Module:** `execution/isolated_executor.py`

### Design Principle

Generated code is never executed within the Streamlit application process. This is a deliberate security decision.

### Level A: Static Validation (enabled)

`StaticValidator` performs checks without executing code:
* Python syntax validation via `ast.parse()`
* JSON structure validation
* HTML structure validation
* Security pattern detection (hardcoded secrets, `eval()`, `exec()`, `shell=True`)
* Patch integrity (no duplicate paths)

### Level B: Isolated Execution (disabled by default)

`IsolatedExecutor` is a stub that always reports `is_available = False`. It returns a clear error message explaining that no verified sandbox is configured.

`SubprocessExecutor` is available only when `ENABLE_CODE_EXECUTION=true` is set in the environment. It is restricted to an allowlist of commands (`python`, `python3`, `pytest`, `pip`) and has a 30-second timeout. It is intended for local development only, not production.

**Future:** To enable Level B safely, integrate a verified sandbox provider (Docker, E2B, Firecracker microVM).

---

## 4. Audit Logging

**Module:** `security/audit.py`

All significant operations are logged as structured JSON-lines events to `data/audit.log` and the SQLite audit table.

### Logged Events

| Event Type | Trigger |
|---|---|
| `file_operation` | File save, delete, rename |
| `provider_call` | LLM API call (with success/error) |
| `security` | Path validation failure, blocked extension |
| `task` | Task state transition, checkpoint creation |
| `project_create` | New project created |
| `project_delete` | Project deleted |
| `project_import` | ZIP imported |

### Event Structure

```json
{
  "timestamp": 1698019200.0,
  "type": "file_operation",
  "actor": "user",
  "details": {
    "action": "save",
    "project_id": "uuid",
    "path": "src/main.py"
  }
}
```

---

## 5. API Key Security

API keys for LLM providers are stored in Streamlit Secrets (`.streamlit/secrets.toml`) or environment variables. They are never:

* Written to the database
* Included in audit logs
* Passed to the LLM as part of prompts
* Committed to git (`.gitignore` excludes `secrets.toml`)

The `.streamlit/secrets.toml.example` file provides a template for required keys without exposing actual values.

---

## 6. Input Validation

### LLM JSON Response Parsing

`utils/json_parser.py` safely parses JSON from LLM responses, handling:
* Markdown code block wrappers
* Leading/trailing whitespace
* Malformed JSON (raises `ProviderError` with `MALFORMED_RESPONSE` category)

### Task State Validation

`workflows/task_state.py` enforces a formal state machine. Invalid transitions (e.g., `pending` to `completed`) raise `ValueError`. This prevents:
* Skipping review steps
* Applying unreviewed changes
* Resuming tasks from invalid states

---

## 7. Threat Model Summary

| Threat | Mitigation | Status |
|---|---|---|
| Path traversal | `resolve_safe_path()` with realpath containment | Implemented + tested |
| Zip bomb | Size limits + entry count limit | Implemented + tested |
| Zip slip | Per-entry path validation in `safe_extract_zip()` | Implemented + tested |
| Malicious file types | Blocked extensions list | Implemented + tested |
| Arbitrary code execution | Disabled by default, allowlist for dev | Implemented |
| API key exposure | Streamlit Secrets / env vars, never logged | Implemented |
| Unreviewed changes | Task state machine enforces review step | Implemented + tested |
| Unbounded LLM costs | Usage tracking with token counts and cost estimates | Implemented |

---

## Testing

Security-related tests:

* `test_path_security.py` - 7 tests covering path traversal, absolute paths, backslash traversal, blocked extensions
* `test_archive_extraction.py` - 4 tests covering zip bombs, zip slip, oversized entries, blocked extensions in archives
* `test_static_validation.py` - 8 tests including security pattern detection (eval, exec, hardcoded secrets, shell=True)