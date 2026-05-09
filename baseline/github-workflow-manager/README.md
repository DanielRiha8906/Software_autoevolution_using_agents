# GitHub Workflow Tracker

A lightweight CLI tool for tracking GitHub Actions workflow runs locally, with JSON persistence.

## Overview

This application represents a baseline workflow management system used in the experimental part of the bachelor thesis focused on software auto-evolution. Its purpose is to model a more infrastructure-oriented software domain than the other baseline applications, namely the local representation and management of GitHub Actions workflow runs.

The system stores metadata about workflow executions, including their identifiers, branches, statuses, conclusions, timestamps, and optional integration-related attributes. Architecturally, the application is divided into model, service, storage, and CLI layers, which makes it suitable for observing how autonomous agents handle evolution in a domain that combines state tracking, filtering, persistence, and operational tooling concerns.

Within the repository, this project serves as one of the reference baseline applications from which evolved variants in `experiments/` are derived.

## Structure

```
github-workflow-tracker/
├── src/
│   ├── __main__.py          # Entry point
│   ├── models/
│   │   ├── workflow_run.py
│   │   ├── workflow_status.py
│   │   └── workflow_conclusion.py
│   ├── services/
│   │   ├── workflow_run_service.py   # Core CRUD + filters
│   │   └── workflow_run_tracker.py  # High-level run creation facade
│   ├── storage/
│   │   └── workflow_json_storage.py  # JSON file persistence
│   └── cli/
│       ├── workflow_cli.py           # argparse CLI
│       └── interactive_menu.py      # Interactive prompt menu
├── tests/
│   ├── test_workflow_run_service.py
│   └── test_workflow_json_storage.py
└── artifacts/
    └── workflow_runs.json   # Created on first run
```

## WorkflowRun fields

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Unique identifier (UUID by default) |
| `workflow_name` | `str` | Name of the workflow |
| `branch` | `str` | Git branch |
| `status` | `WorkflowStatus` | `queued`, `in_progress`, `completed`, `waiting`, `requested`, `pending` |
| `conclusion` | `WorkflowConclusion \| None` | `success`, `failure`, `cancelled`, `skipped`, `timed_out`, `action_required`, `neutral`, `stale` |
| `created_at` | `datetime` | UTC timestamp |
| `updated_at` | `datetime \| None` | UTC timestamp |
| `run_number` | `int \| None` | GitHub run number |
| `commit_sha` | `str \| None` | Commit SHA |

## Usage

### Interactive menu

```bash
cd github-workflow-tracker
python -m src
```

### CLI

```bash
# Add a run
python -m src add --name "CI" --branch main --status completed --conclusion success --run-number 42 --commit-sha abc123

# List all runs
python -m src list

# Filter by branch
python -m src list --branch main

# Filter by status
python -m src list --status completed

# Filter by conclusion
python -m src list --conclusion failure

# Get run detail
python -m src detail <run-id>
```

## Tests

```bash
pytest tests/
```
