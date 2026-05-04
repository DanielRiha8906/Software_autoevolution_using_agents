# Task 10 Analysis: GUI Implementation using Tkinter

## Task Summary
Implement a GUI using tkinter (Python stdlib) for the TODO application. The GUI must:
- Display: title, status, due date, project
- Support operations: view, add, change status, delete
- Highlight overdue tasks visually
- Call existing service layer logic (no business logic duplication)
- Support filtering by status or project
- Bonus: comments support and comment count
- Be launchable via `python -m src --gui`

---

## Current Architecture Summary

### Layer Structure (from Phase 1 refactoring)
```
Entry Point (__main__.py)
    ├── Interactive Menu (cli/interactive_menu.py) → calls TodoService
    ├── Command-line CLI (cli/todo_cli.py) → calls TodoService
    └── [NEW] GUI (TBD) → calls TodoService

TodoService (services/todo_service.py) [PUBLIC API]
    ├── Internal: TaskManager
    ├── Internal: ProjectManager
    └── Internal: ImportValidator

Models (no dependencies)
    ├── Task (id, title, description, status, created_at, updated_at, due_date, comments, project_id)
    ├── TaskStatus (enum: PENDING, IN_PROGRESS, DONE)
    ├── TaskComment (id, task_id, content, created_at, author, updated_at)
    ├── Project (id, name)
    └── TaskSummaryReport

Storage Layer
    └── JsonStorage (path-based JSON persistence)
```

### Key Design Constraints
- Only TodoService is exported from services module
- Exception hierarchy in services/exceptions.py: ServiceError, TaskNotFoundError, ProjectNotFoundError
- All models are simple dataclasses with to_dict()/from_dict() serialization
- Models have query methods like is_overdue(), is_pending(), is_in_progress(), is_completed()
- No circular dependencies; models import nothing

---

## Existing Service Layer API (Public Methods)

### Task Operations
- `add_task(title, description=None, due_date=None) → Task`
- `get_task(task_id) → Task`
- `list_tasks(status=None, before=None, after=None, overdue_only=False) → List[Task]`
- `list_tasks_by_project(project_id) → List[Task]`
- `update_task(task_id, title=None, description=None, due_date=None) → Task`
- `start_task(task_id) → Task`  [mark IN_PROGRESS]
- `complete_task(task_id) → Task`  [mark DONE]
- `reopen_task(task_id) → Task`  [mark IN_PROGRESS]
- `set_due_date(task_id, due_date) → Task`
- `delete_task(task_id) → None`

### Project Operations
- `create_project(name) → Project`
- `list_projects() → List[Project]`
- `get_project(project_id) → Project`
- `delete_project(project_id) → None`
- `move_task_to_project(task_id, project_id) → Task`

### Comment Operations
- `add_comment(task_id, content, author=None) → TaskComment`
- `get_comments(task_id) → List[TaskComment]`
- `delete_comment(task_id, comment_id) → None`
- `edit_comment(task_id, comment_id, content) → TaskComment`

### Query Methods (on Task model)
- `task.is_overdue() → bool`
- `task.is_pending() → bool`
- `task.is_in_progress() → bool`
- `task.is_completed() → bool`
- `task.status` (enum: PENDING, IN_PROGRESS, DONE)
- `task.due_date` (Optional[datetime])

---

## GUI Components to Create

### 1. New GUI Module
**Location:** `src/gui/` (new directory)

**Files to create:**
- `src/gui/__init__.py` — package marker
- `src/gui/todo_gui.py` — main GUI application class
- `src/gui/widgets.py` (optional, for reusable components)

### 2. TodoGUI Main Class
Responsibilities:
- Initialize Tkinter root window
- Create frames for task list, filters, details
- Instantiate TodoService with default or custom storage
- Handle window layout and geometry
- Entry point: `TodoGUI.run()` or `TodoGUI.mainloop()`

### 3. Core GUI Widgets/Frames

#### Task List Frame
- Treeview (table) with columns: [Status checkbox], Title, Due Date, Project, Comment Count
- Sortable by column
- Row selection to view/edit details
- Visual highlight for overdue tasks (red background or icon)

#### Task Details Panel
- Display: title, description, status (dropdown), due date (calendar or text), project (dropdown)
- Edit buttons for each field
- Comments section: list + add/edit/delete UI

#### Filter Controls
- Buttons/dropdowns: Show All, Pending, In Progress, Done
- Project filter dropdown
- Clear/Reset filters button
- Overdue-only toggle

#### Action Buttons
- Add Task (opens dialog)
- Edit Selected Task
- Delete Selected Task
- Refresh

#### Add/Edit Task Dialog
- Modal form for task creation/update
- Fields: title (required), description (optional), due date (optional), project (optional)
- Buttons: Save, Cancel

---

## Files That Need Modification

### 1. src/__main__.py
**Current:** Routes to CLI or InteractiveMenu based on sys.argv presence
**Required changes:**
- Add `--gui` flag parsing
- Instantiate TodoGUI and call run() if `--gui` present
- Maintain backward compatibility: no args → interactive menu, args with CLI → CLI mode

```python
# Pseudo-logic:
if '--gui' in sys.argv:
    from .gui.todo_gui import TodoGUI
    TodoGUI().run()
elif len(sys.argv) > 1:
    TodoCLI().run()  # existing
else:
    InteractiveMenu().run()  # existing
```

### 2. src/gui/__init__.py
**New file**
- Export TodoGUI

---

## Dependencies Analysis

### Current Dependencies
- **stdlib only**: dataclasses, datetime, uuid, json, pathlib, argparse, enum
- **No external packages currently required**

### New Dependencies for GUI
- **tkinter** — Python stdlib (no pip install needed)
  - Available in Python 3.7+
  - May need separate install on Linux: `apt-get install python3-tk`
  - But this is NOT a blocker for the code implementation

### No new pip dependencies required

---

## Key Implementation Details to Note

### 1. Overdue Visual Highlighting
- Use Task.is_overdue() → returns bool if due_date < now and status != DONE
- Tkinter: use Treeview tag configuration for background color (red/orange)
- Apply tag to row during data population:
  ```python
  tree.insert(parent, 'end', values=(...), tags=('overdue',) if task.is_overdue() else ())
  tree.tag_configure('overdue', background='#ffcccc')
  ```

### 2. Status Representation
- TaskStatus enum has three values: PENDING, IN_PROGRESS, DONE
- Display as: "Pending", "In Progress", "Done" (humanized)
- Status dropdown for editing should use enum values or humanized names

### 3. Comment Count Display
- Task.comments is a List[TaskComment]
- Display len(task.comments) in table column
- Bonus: comment count badge/indicator

### 4. Filtering Architecture
- Service layer already supports:
  - `list_tasks(status=None, before=None, after=None, overdue_only=False)`
  - `list_tasks_by_project(project_id)`
- GUI filters should map to these calls
- Combine filters: e.g., status=PENDING + project_id=P123

### 5. Data Refresh Pattern
- Populate Treeview/UI elements from service calls
- After add/edit/delete, refresh the task list
- Consider caching or on-demand refresh

### 6. Error Handling
- TodoService raises TaskNotFoundError, ProjectNotFoundError, ValueError
- Catch and display in GUI (messagebox or status bar)
- Do NOT let exceptions crash the GUI

### 7. Date Handling
- Task.due_date is Optional[datetime] with timezone awareness (UTC)
- Tkinter has no native date picker; options:
  - Use a simple ISO 8601 text entry with validation
  - Use tkcalendar (external dep) if desired
  - Parse/format with datetime.fromisoformat()
  - **Recommendation:** Text entry + validation or simple picker widget

### 8. GUI Launch Entry Point
- `python -m src --gui` must work
- Modify __main__.py to detect --gui flag
- Create TodoGUI() and call .run() or .mainloop()

---

## Scope Signals

### In Scope
- Core CRUD for tasks via GUI
- Status change (Pending → In Progress → Done)
- Due date display and filtering
- Project assignment and filtering
- Comments view/add/edit/delete (bonus)
- Overdue highlighting
- Service layer integration (no business logic duplication)
- Launchable via `python -m src --gui`

### Explicitly Out of Scope
- Export/Import through GUI (CLI-only feature for now)
- Advanced date pickers (use text input or stdlib only)
- Task search/full-text (not in requirements)
- Multiple window/MDI interface (single window)
- Drag-and-drop task reordering
- Dark theme/theme switching

### Borderline / Not Explicitly Mentioned
- Persistence auto-save (service already handles via JsonStorage)
- Undo/Redo (not required)
- Keyboard shortcuts (optional, nice-to-have)
- Task categories beyond Project (not mentioned, so skip)

---

## Suggested Priorities

### Priority 1: Foundation (Critical for Core Functionality)
1. Create `src/gui/todo_gui.py` with TodoGUI class
2. Implement basic window layout with frames
3. Create TaskListFrame with Treeview showing tasks
4. Implement task list population from TodoService.list_tasks()
5. Modify `src/__main__.py` to support `--gui` flag
6. Test: `python -m src --gui` launches window

### Priority 2: Core Operations (Required)
1. Task filtering UI (status, project, overdue buttons)
2. Add Task dialog (modal, collect title/description/due_date/project)
3. Delete Task operation (selection → delete → refresh)
4. Edit Task: change status (Pending → In Progress → Done buttons)
5. Update due date and project for selected task

### Priority 3: Task Details & Comments (Core with Bonus)
1. Task details panel (show selected task metadata)
2. Comments list display (comment count in table)
3. Add comment dialog
4. Delete comment from UI
5. Edit comment dialog

### Priority 4: Polish & Validation
1. Overdue task visual highlighting (red background/tag)
2. Error handling and messagebox notifications
3. UI responsiveness and layout refinement
4. Timezone handling for due dates (validate ISO 8601 or use calendar widget)
5. Date formatting (display human-readable, store ISO)

### Priority 5: Optional Enhancements
1. Keyboard shortcuts (e.g., Ctrl+N for new task)
2. Task description preview in details pane
3. Refresh button / auto-refresh
4. Status bar with summary stats
5. Window geometry persistence

---

## Testing Strategy

### Unit Tests (existing test patterns)
- Test TodoGUI initialization with custom storage
- Mock TodoService to test GUI behavior without persistence
- Test filter logic: status, project, overdue

### Integration Tests
- Launch GUI with real TodoService
- Add task, verify it appears in list
- Edit task, verify changes reflected
- Delete task, verify removal from UI
- Filter by status/project, verify correct tasks shown

### Manual Verification
- `python -m src --gui` launches window
- All operations work without raising unhandled exceptions
- Overdue tasks are highlighted
- Comment count displays correctly
- No CLI mode breakage (test `python -m src list`, interactive menu)

---

## File Structure After Implementation

```
experiments/pipeline/user_stories/TODO/
├── src/
│   ├── __init__.py
│   ├── __main__.py               [MODIFIED: add --gui flag handling]
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── todo_cli.py
│   │   └── interactive_menu.py
│   ├── gui/                      [NEW DIRECTORY]
│   │   ├── __init__.py           [NEW: export TodoGUI]
│   │   └── todo_gui.py           [NEW: main GUI implementation]
│   ├── models/
│   │   ├── __init__.py
│   │   ├── task.py
│   │   ├── task_status.py
│   │   ├── task_comment.py
│   │   ├── project.py
│   │   └── task_summary_report.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── todo_service.py
│   │   ├── task_manager.py
│   │   ├── project_manager.py
│   │   └── import_validator.py
│   └── storage/
│       ├── __init__.py
│       └── json_storage.py
├── tests/
│   ├── __init__.py
│   ├── test_*.py (existing)
│   └── test_gui.py               [NEW: GUI unit/integration tests]
└── artifacts/
    └── *.puml (diagrams)
```

---

## Ambiguities & Assumptions

### 1. Date Picker Approach
**Ambiguity:** Task 10 says "due date" but doesn't specify UI widget.
**Assumption:** Use text entry field with ISO 8601 validation. If more sophisticated picker needed, tkcalendar can be added in future without breaking core.

### 2. Comment Display Context
**Ambiguity:** Task says "comments support and comment count" as bonus, but doesn't detail comment UI.
**Assumption:** Display comment count in table; separate comments section in details pane. Full CRUD for comments is included as part of bonus.

### 3. Filtering Combination
**Ambiguity:** Can filters be combined (e.g., status=PENDING AND project=ProjectA)?
**Assumption:** Yes. Service supports this via list_tasks(status=X) then filter by project, or use list_tasks_by_project() with post-filter by status.

### 4. Auto-Save vs. Manual Save
**Ambiguity:** Should edits auto-save or require explicit save?
**Assumption:** Edits should call service immediately (immediate persistence via JsonStorage). No unsaved changes buffer.

### 5. Window Geometry & State
**Ambiguity:** Should window size/position persist across sessions?
**Assumption:** Not required. Each launch starts fresh. Can be added in future if needed.

### 6. Task Selection State
**Ambiguity:** Should selecting a task auto-scroll to details pane?
**Assumption:** Yes. Double-click or single-select should populate details panel on the right/below.

---

## Conclusion

This analysis identifies:
- **What exists:** Solid service layer (TodoService), models, and storage. No GUI layer yet.
- **What's needed:** TodoGUI class with Tkinter windows, frames, and widgets. Entry point modification for --gui flag.
- **What's reusable:** All TodoService methods; no business logic needs duplication.
- **No new dependencies:** tkinter is stdlib; no pip packages required.
- **Key technical notes:** 
  - Overdue highlighting via Treeview tags
  - Error handling via messagebox
  - Date validation with ISO 8601 strings
  - Filter combinations via multiple service calls
  - Timezone-aware datetime handling already in place

Proceed to system-architect phase for detailed implementation design.
