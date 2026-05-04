# Calculator Project - Task 10 Analysis
# Add Graphical User Interface Using tkinter

**Task 10: Add a graphical user interface using tkinter**
**Status:** Analysis Complete
**Date:** 2026-05-04

---

## Task Summary

Add a complete tkinter-based graphical user interface (GUI) to the calculator application. The GUI must:
- Provide an alternative to the CLI for all calculator operations
- Support both standard mode (8 operations) and scientific mode (6 additional operations)
- Display and manage calculation memory/history
- Integrate seamlessly with existing architecture (services, storage, models)
- Be optional—existing CLI functionality unchanged
- Be invoked via a new CLI flag or menu option

---

## Current State: Code Structure

### Directory Structure
```
src/
├── __main__.py                    # Entry point, argparse, CLI wiring
├── models/                        # Domain models (read-only data)
│   ├── operation.py               # Operation enum (14 operations total)
│   ├── calculation_result.py       # Result dataclass (successful calcs only)
│   ├── memory_entry.py            # MemoryEntry dataclass (success + failure)
│   └── calculation_statistics.py   # Statistics aggregation
├── services/                      # Business logic (read via protocol interfaces)
│   ├── calculator.py              # Pure calculation engine
│   ├── calculator_service.py       # Orchestrates Calculator + JsonStorage
│   └── memory_service.py          # Query/analytics over MemoryEntry
├── storage/                       # Persistence (read/write JSON)
│   ├── json_storage.py            # Persists CalculationResult
│   └── memory_json_storage.py     # Persists MemoryEntry
├── protocols/                     # Abstract interfaces (NEW as of Task 09)
│   └── __init__.py                # Storage[T], CalculationService, MemoryService protocols
└── cli/
    └── calculator_cli.py          # Interactive menu + one-shot CLI
```

### Current Architecture Layers

**1. Calculation Engine (Pure)**
- `Calculator`: 14 stateless methods (add, subtract, multiply, divide, square, sqrt, power, modulo, sin, cos, tan, log, ln, exp)
- Error-handling: raises `ValueError` for invalid inputs
- No dependencies on services or storage

**2. Services (Orchestration)**
- `CalculatorService`: Execute calc → save to `JsonStorage` → return `CalculationResult`
- `MemoryService`: Manage `MemoryEntry` audit trail with filtering, statistics, import/export
- Both services depend on `Storage[T]` protocol, not concrete classes

**3. Storage (Persistence)**
- `JsonStorage`: Append-only JSON file for `CalculationResult` → `artifacts/calculations.json`
- `MemoryJsonStorage`: Append-only JSON file for `MemoryEntry` → `artifacts/memory_entries.json`
- Both implement `Storage[T]` protocol

**4. Interface (Current)**
- `CalculatorCLI`: Interactive menu (14 operations) + memory features + one-shot flags
- Menu structure: 1-14 operations, 15-22 admin (memory, statistics, export, import, exit)
- Entry point: `src/__main__.py` → argparse setup → CLI instantiation

---

## Key Domain Concepts

### Operation Enum
**File:** `src/models/operation.py`

```python
class Operation(Enum):
    # Standard (8)
    ADD, SUBTRACT, MULTIPLY, DIVIDE,
    SQUARE, SQRT, POWER, MODULO,
    
    # Scientific (6)
    SIN, COS, TAN, LOG, LN, EXP
```

- `from_string(value: str)` → parses "add", "subtract", etc.
- `display_name()` → returns "Add", "Subtract", etc.
- Used to dispatch in `Calculator.calculate()`

### CalculationResult
**File:** `src/models/calculation_result.py`

Represents a **successful calculation only**.

```python
@dataclass
class CalculationResult:
    operation: str               # operation name ("add", "sqrt", etc.)
    operand_a: float
    operand_b: float
    result: float               # computed value
    timestamp: str              # ISO format
    execution_time_ms: float    # milliseconds
    
    def __str__() → "a + b = c"  # formatted for display
```

Persisted to `artifacts/calculations.json` (append-only).

### MemoryEntry
**File:** `src/models/memory_entry.py`

Represents **any calculation attempt** (success or failure).

```python
@dataclass
class MemoryEntry:
    operation: str               # operation name
    operand_a: float
    operand_b: float
    result: Optional[float]      # None if failed
    success: bool                # True/False
    error_message: Optional[str] # error details if failed
    execution_timestamp: str     # ISO format
    execution_time_ms: float
    memory_entry_id: str         # UUID auto-generated
    
    def __str__() → "operation: inputs → result|error"
```

Persisted to `artifacts/memory_entries.json` (append-only).
Auto-records successful calculations (manually) and can be extended to record failures.

### CalculationStatistics
**File:** `src/models/calculation_statistics.py`

Aggregated metrics over all `MemoryEntry` records:

```python
@dataclass
class CalculationStatistics:
    operation_counts: dict[str, int]         # usage by operation
    total_calculations: int
    error_count: int
    error_percentage: float
    average_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    per_operation_stats: dict[str, dict]     # per-op breakdown
```

Computed on-demand by `MemoryService.compute_statistics()`.

---

## Standard Mode vs Scientific Mode

**Standard Mode Operations (8):**
1. Add
2. Subtract
3. Multiply
4. Divide (with zero-check)
5. Square (unary)
6. Square Root (unary, with negative-check)
7. Power
8. Modulo (with zero-check)

**Scientific Mode Operations (6):**
9. Sin (unary, radians)
10. Cos (unary, radians)
11. Tan (unary, radians)
12. Log (base 10, unary, with domain-check a > 0)
13. Ln (natural log, unary, with domain-check a > 0)
14. Exp (unary)

**Mode Transition:**
- In CLI: unified menu, all 14 operations always available
- **In GUI: likely organized as two tabs or sections**
  - Standard tab: 8 operations
  - Scientific tab: 6 operations
  - Both tabs share the same services and memory

---

## How MemoryEntry Records Work

### Creation
1. After a successful calculation via `CalculatorService.perform()`, a `CalculationResult` is created and saved
2. Separately, a `MemoryEntry` must be manually created and passed to `MemoryService.store()`
3. `MemoryEntry.__post_init__()` auto-generates:
   - `execution_timestamp` (ISO format)
   - `memory_entry_id` (UUID)

### Storage
- `MemoryService.store(entry)` delegates to `MemoryJsonStorage.save(entry)`
- `MemoryJsonStorage.save()` appends entry to `artifacts/memory_entries.json`
- File is created automatically if missing

### Retrieval & Querying
- `MemoryService.retrieve_all()` → loads all entries from JSON
- `filter_by_operation(name)` → case-insensitive operation filter
- `filter_by_success(bool)` → filter by success/failure
- `filter_by_execution_time(min_ms, max_ms)` → time range filter
- `compute_statistics()` → aggregate metrics

### Display
- `MemoryEntry.__str__()` → "operation: a and b → result" (or error message)
- Used in CLI menu option 10 ("View memory")

---

## Service Layer Architecture (Key for GUI Integration)

### Services Depend on Protocols
As of Task 09, services use abstract protocol interfaces (not concrete classes):

**CalculationService Protocol:**
```python
class CalculationService(Protocol):
    def perform(self, operation: Operation, a: float, b: float) -> CalculationResult: ...
    def get_history(self) -> List[CalculationResult]: ...
```

**MemoryService Protocol:**
```python
class MemoryService(Protocol):
    def store(self, entry: MemoryEntry) -> None: ...
    def retrieve_all(self) -> List[MemoryEntry]: ...
    def filter_by_operation(self, name: str) -> List[MemoryEntry]: ...
    def filter_by_success(self, bool) -> List[MemoryEntry]: ...
    def compute_statistics(self) -> CalculationStatistics: ...
    def export_to_file(self, path) -> int: ...
    def import_from_file(self, path, skip_invalid) -> tuple[int, list]: ...
```

### Concrete Service Classes (Wired in `src/__main__.py`)
- `CalculatorService(Calculator, JsonStorage)` implements `CalculationService`
- `MemoryService(MemoryJsonStorage)` implements `MemoryService`

**GUI Integration Point:**
- GUI can use same service instances created in `__main__.py`
- Or GUI can be passed service instances at init time
- Services are stateless (except for file I/O); safe to share

---

## Current CLI Structure (Reference)

**Entry point:** `src/__main__.py`

```python
def main() -> None:
    parser = argparse.ArgumentParser(...)
    # Flags: --operation OP A B, --memory, --statistics, --export, --import, etc.
    
    service = _build_service()           # CalculatorService instance
    memory_service = _build_memory_service()  # MemoryService instance
    cli = CalculatorCLI(service, memory_service)
    
    if args.export:
        cli.export_memory(...)
    elif args.import_file:
        cli.import_memory(...)
    elif args.memory_filter:
        memory_service.filter_by_*()
    elif args.statistics:
        cli.show_statistics()
    elif args.memory:
        cli.show_memory()
    elif args.operation:
        cli.run_command(...)
    else:
        cli.run_interactive()  # Interactive menu loop
```

**Interactive Menu (`CalculatorCLI.run_interactive()`):**
```
=== Calculator ===
Operations:
  1. Add
  2. Subtract
  ...
  14. Exp
  15. View history
  16. View memory
  17. Filter memory by operation
  18. Filter memory by status
  19. View statistics
  20. Export memory to file
  21. Import memory from file
  22. Exit

Choose option: [user enters number 1-22]
```

---

## Task 10 Requirements Analysis

### Must Have

1. **Graphical Interface**
   - tkinter-based window application
   - No CLI knowledge required; pure GUI
   - Professional, user-friendly layout
   - Responsive to user interactions

2. **Standard Mode Operations (All 8)**
   - Accessible buttons or menu for: Add, Subtract, Multiply, Divide, Square, Square Root, Power, Modulo
   - Input fields for operands (a, b)
   - Display result after calculation
   - Show error messages on invalid input (e.g., divide by zero, negative sqrt)

3. **Scientific Mode Operations (All 6)**
   - Accessible buttons or menu for: Sin, Cos, Tan, Log, Ln, Exp
   - Handle unary operations (ignore operand_b or hide it)
   - Input fields for operand(s)
   - Display result; handle domain errors (log/ln of non-positive)

4. **Mode Switching**
   - User can switch between Standard and Scientific modes
   - Likely implemented as:
     - Tabs (one for Standard, one for Scientific)
     - Or mode toggle button with dynamic UI update
   - All 14 operations eventually reachable

5. **Calculation Memory Display**
   - Show all stored memory entries (from `MemoryService.retrieve_all()`)
   - Display in a scrollable list or table
   - Show: operation, operands, result/error, timestamp
   - Update automatically after new calculation

6. **Statistics Display**
   - Display aggregated stats (from `MemoryService.compute_statistics()`)
   - Show: total calculations, error count, error %, execution times, per-operation breakdown
   - Update automatically after new calculation

7. **Entry Point & Invocation**
   - GUI accessible via new CLI flag: `python -m src --gui` or similar
   - Or: interactive menu option to launch GUI (if maintaining backward compatibility)
   - Must not break `python -m src` (existing interactive mode)

### Should Have

1. **Seamless Service Integration**
   - GUI uses the same `CalculatorService` and `MemoryService` instances as CLI
   - Shared storage; if CLI runs afterward, memory is consistent
   - No duplicate storage mechanisms

2. **Clear Presentation**
   - Consistent with domain terminology (operation names, field names)
   - Easy to understand operation categories (Standard vs Scientific)
   - Readable memory/statistics output

3. **Error Handling**
   - Validation of numeric inputs before calling service
   - Display user-friendly error messages (not stack traces)
   - Graceful handling of invalid operation selections

4. **Consistency**
   - Operation behavior identical to CLI version
   - Memory entries created with same metadata (timestamp, execution_time)
   - Statistics computed the same way

### Could Have

1. **Export/Import GUI**
   - GUI buttons to export memory to file / import from file
   - File dialogs for path selection
   - Success/error feedback

2. **Memory Filtering GUI**
   - Filter controls (operation name, success/failure)
   - Display filtered subset in memory list
   - Multiple filter combinations

3. **Calculation History (short-term)**
   - Display recent calculations from `CalculatorService.get_history()` separately
   - Distinction between short-term history and long-term memory

4. **Keyboard Support**
   - Numeric keypad for input
   - Operation shortcuts (e.g., Alt+A for Add)
   - Enter to execute calculation

5. **Theme/Appearance**
   - Dark mode option
   - Configurable button sizes
   - Resizable window

### Won't Have (Explicitly Out of Scope)

1. **Complex Equation Parsing**
   - No support for "3 + 5 * 2" expressions
   - Only single operation per calculation (a OP b)

2. **Additional Operations**
   - No new arithmetic operations beyond the 14 already defined
   - No custom user-defined operations

3. **Database Backend**
   - Keep using existing JSON file storage
   - No migration to SQL or other DB

4. **Networking**
   - No cloud sync, no remote calculations
   - GUI operates locally only

5. **Embedded Documentation**
   - No help text or tutorials in GUI
   - Keep minimal UI; users know calculator basics

---

## Key Integration Points

### 1. Service Initialization in `__main__.py`
Currently:
```python
def _build_service() -> CalculatorService:
    storage_path = Path(__file__).parent.parent / "artifacts" / "calculations.json"
    return CalculatorService(Calculator(), JsonStorage(storage_path))

def _build_memory_service() -> MemoryService:
    memory_storage_path = Path(__file__).parent.parent / "artifacts" / "memory_entries.json"
    return MemoryService(MemoryJsonStorage(memory_storage_path))
```

**GUI Impact:**
- Same service instances need to be passed to GUI window
- Or GUI can create its own (but then memory won't be shared with CLI)
- Recommended: Pass existing instances to GUI class

### 2. Model Usage
- **CalculationResult**: Read-only; GUI displays operation, operands, result, timestamp, execution_time
- **MemoryEntry**: GUI creates new instances after successful calculations, stores via `memory_service.store()`
- **CalculationStatistics**: GUI displays results from `memory_service.compute_statistics()`
- **Operation**: GUI provides UI for selecting from enum; uses `Operation.from_string()` and `display_name()`

### 3. Service Method Calls
GUI must call:
- `calculator_service.perform(operation, a, b)` → returns `CalculationResult` or raises `ValueError`
- `memory_service.store(entry)` → stores `MemoryEntry`
- `memory_service.retrieve_all()` → gets all `MemoryEntry` objects
- `memory_service.compute_statistics()` → gets `CalculationStatistics`
- Optional: `memory_service.filter_by_operation()`, etc.
- Optional: `memory_service.export_to_file()`, `import_from_file()`

### 4. Error Handling
- `Calculator` and services raise `ValueError` on invalid input
- GUI must catch, format, and display errors in message boxes or status labels
- Example: `except ValueError as e: messagebox.showerror("Error", str(e))`

---

## File Structure Changes Required

### New Files

1. **`src/gui/` (new package)**
   ```
   src/gui/
   ├── __init__.py                # GUI package initialization
   ├── calculator_gui.py          # Main GUI window class (CalculatorGUI)
   ├── standard_mode_tab.py       # Standard operations tab (optional refactor)
   └── scientific_mode_tab.py     # Scientific operations tab (optional refactor)
   ```

   **Alternative (simpler):**
   ```
   src/gui/
   ├── __init__.py
   └── calculator_gui.py          # All GUI code in single file
   ```

2. **`src/gui/calculator_gui.py`**
   - Main class: `CalculatorGUI(tk.Tk)`
   - Constructor: `__init__(service: CalculationService, memory_service: MemoryService)`
   - Methods:
     - `_create_standard_mode_frame()` → buttons for 8 standard operations
     - `_create_scientific_mode_frame()` → buttons for 6 scientific operations
     - `_on_operation_button_click(operation: Operation)` → handler for operation buttons
     - `_prompt_operands()` → get a, b from input fields (or dialog)
     - `_execute_calculation()` → call service, update memory, display result
     - `_refresh_memory_display()` → update memory list widget
     - `_refresh_statistics_display()` → update stats widget
     - `_show_error(message)` → display error dialog/label
     - Lifecycle: `run()` to start event loop

### Modified Files

1. **`src/__main__.py`**
   - Add new CLI flag: `--gui` or `--launch-gui`
   - Add logic to instantiate `CalculatorGUI` if flag is set
   - Pass service instances to GUI
   - Keep existing CLI logic unchanged

2. **`src/cli/calculator_cli.py`**
   - Optional: Add menu option to launch GUI (if desired for backward compat)
   - Or: Keep as-is, GUI is separate entry point

### Unchanged

- `src/models/` — no changes
- `src/services/` — no changes
- `src/storage/` — no changes
- `src/protocols/` — no changes
- `tests/` — no new tests required (GUI is presentation layer; services are tested separately)

---

## Possible GUI Layouts

### Option A: Tab-Based (Recommended for Task 10)

```
┌────────────────────────────────────────────┐
│  OOP Calculator - GUI                      │
├────────────────────────────────────────────┤
│  [Standard] [Scientific]                   │  <- Tabs
├────────────────────────────────────────────┤
│                                            │
│  Operation: [Dropdown/Buttons]             │
│  Operand A: [Input field]                  │
│  Operand B: [Input field]     [Calculate] │
│                                            │
│  Result: [Display result or error]         │
│                                            │
│  ┌────────────────────────────────────┐   │
│  │ Memory Entries                     │   │
│  │ ──────────────────────────────     │   │
│  │ 1. add: 3 and 5 → 8                │   │
│  │ 2. multiply: 2 and 3 → 6           │   │
│  │ 3. divide: 10 and 0 → Error: ... │   │
│  │ [Scroll bar]                       │   │
│  └────────────────────────────────────┘   │
│                                            │
│  Statistics                                │
│  ──────────────────                       │
│  Total Calculations: 3                     │
│  Error Count: 1                            │
│  Avg Execution Time: 0.15 ms               │
│                                            │
│  [Export] [Import] [Clear] [Exit]         │
└────────────────────────────────────────────┘
```

### Option B: Side-by-Side (Alternative)

```
┌──────────────────────────────────────────────────────────┐
│ OOP Calculator - GUI                                      │
├──────────────────┬──────────────────────────────────────┤
│ Standard         │ Operand A: [field]                   │
│ ──────────────── │ Operand B: [field]                   │
│ [Add]  [Subtract]│ Operation: [Dropdown]                │
│ [Mul]  [Divide]  │                                      │
│ [Sqrt] [Square]  │ [Calculate] [Clear]                  │
│ [Power] [Modulo] │                                      │
│                  │ Result: [Display]                    │
│ Scientific       │                                      │
│ ──────────────── │ Memory Entries                       │
│ [Sin]  [Cos]     │ ────────────────                     │
│ [Tan]  [Log]     │ [List of entries]                    │
│ [Ln]   [Exp]     │                                      │
│                  │ Statistics: [Compact display]       │
│ [Export] [Import]│ [Export] [Import] [Exit]            │
└──────────────────┴──────────────────────────────────────┘
```

### Option C: Button Grid (Alternative)

```
┌────────────────────────────────────┐
│ OOP Calculator - GUI               │
├────────────────────────────────────┤
│ A: [field]  B: [field]  [Standard] │
│ [Scientific]                       │
│                                    │
│  [Add] [Sub] [Mul] [Div]           │
│ [Sqrt][Sq] [Pow] [Mod]             │
│                                    │
│ (Scientific shown when toggled)    │
│  [Sin] [Cos] [Tan]                 │
│ [Log] [Ln] [Exp]                   │
│                                    │
│ Result: [Display]                  │
│                                    │
│ Memory: [Scrollable list]          │
│ Stats:  [Summary]                  │
│                                    │
│ [Export] [Import] [Clear] [Exit]   │
└────────────────────────────────────┘
```

---

## Standard Mode Understanding (Current Code)

From `src/models/operation.py`, the 8 standard operations are:
1. **ADD** (value="add") → Calculator.add(a, b)
2. **SUBTRACT** (value="subtract") → Calculator.subtract(a, b)
3. **MULTIPLY** (value="multiply") → Calculator.multiply(a, b)
4. **DIVIDE** (value="divide") → Calculator.divide(a, b) [raises ValueError if b == 0]
5. **SQUARE** (value="square") → Calculator.square(a, b) [returns a²; ignores b]
6. **SQRT** (value="sqrt") → Calculator.sqrt(a, b) [returns √a; raises ValueError if a < 0]
7. **POWER** (value="power") → Calculator.power(a, b) [returns a^b]
8. **MODULO** (value="modulo") → Calculator.modulo(a, b) [raises ValueError if b == 0]

**Operand Semantics:**
- Binary operations: both a and b are required and used
- Unary operations (square, sqrt, sin, cos, tan, log, ln, exp): only `a` is used; `b` is ignored/optional

---

## MemoryEntry Records Understanding

### What Gets Stored
When a calculation succeeds:
1. `CalculatorService.perform(operation, a, b)` executes and saves `CalculationResult` to `artifacts/calculations.json`
2. GUI can manually create `MemoryEntry` and call `memory_service.store(entry)` to append to `artifacts/memory_entries.json`

Example flow (desired for GUI):
```python
try:
    result = calculator_service.perform(operation, a, b)
    # Success: create memory entry
    entry = MemoryEntry(
        operation=operation.value,
        operand_a=a,
        operand_b=b,
        result=result.result,
        success=True,
        error_message=None,
        execution_timestamp="",  # auto-filled in __post_init__
        execution_time_ms=result.execution_time_ms,
        memory_entry_id=None     # auto-generated UUID in __post_init__
    )
    memory_service.store(entry)
except ValueError as e:
    # Failure: could create memory entry with success=False
    entry = MemoryEntry(
        operation=operation.value,
        operand_a=a,
        operand_b=b,
        result=None,
        success=False,
        error_message=str(e),
        execution_timestamp="",
        execution_time_ms=0.0,
        memory_entry_id=None
    )
    memory_service.store(entry)
```

### Why MemoryEntry Matters
- `MemoryEntry` is the complete audit trail (success + failure)
- `CalculationResult` only captures successful calcs
- `MemoryService` provides querying, filtering, statistics over all entries
- Memory entries are persisted across sessions (JSON file)

---

## Ambiguities and Working Assumptions

### 1. **Should the GUI automatically record failures to memory?**
   - **Current CLI behavior:** Failures are not recorded; only successes go to `CalculatorService` and then to memory
   - **Assumption for GUI:** Same behavior as CLI—only successful calcs are recorded to memory
   - **Implication:** GUI catch block shows error dialog but does NOT store failure entry

### 2. **How should mode switching work (Standard vs Scientific)?**
   - **Option A (Tabs):** Two tkinter.Frame objects on Notebook widget; user clicks tabs to switch
   - **Option B (Button toggle):** Single frame; buttons dynamically replaced or hidden when toggling
   - **Option C (Sidebar menu):** Vertical menu; operations listed; user selects operation name
   - **Assumption for this analysis:** Use **Option A (Tabs)** as clearest UI pattern
   - **Implication:** Import `tkinter.ttk.Notebook` for tab widget

### 3. **Should operand B be hidden for unary operations in the GUI?**
   - **Option A:** Always show two input fields (A and B); for unary, user ignores B
   - **Option B:** Hide operand B when unary operation is selected
   - **Option C:** Dynamically update UI layout based on operation
   - **Assumption:** Use **Option A** (simpler; unary operations ignore B anyway)
   - **Implication:** Label can say "Operand B (ignored for unary operations)" or similar

### 4. **Should memory entries include failed calculations?**
   - **Current state:** Only successes are stored by CLI
   - **Assumption:** Keep same behavior in GUI—only record successful calcs to memory
   - **Future task:** If error recording is desired, a separate task should add that

### 5. **Entry point: `--gui` flag vs menu option vs separate script?**
   - **Option A:** `python -m src --gui` — add flag to argparse in `__main__.py`
   - **Option B:** `python -m src` interactive menu with "Launch GUI" option
   - **Option C:** Separate entry point script (e.g., `run_gui.py`)
   - **Assumption:** Use **Option A** (`--gui` flag) for clarity
   - **Implication:** Modify `__main__.py` to detect flag and instantiate `CalculatorGUI`

### 6. **Should the GUI window block the CLI exit?**
   - **Current behavior:** CLI with `--operation` flag completes immediately
   - **Option A:** `python -m src --gui` starts GUI event loop; block until window closes
   - **Option B:** Start GUI in background thread; return immediately
   - **Assumption:** Use **Option A** (simpler, expected behavior for GUI apps)
   - **Implication:** GUI's `mainloop()` blocks until user closes window

### 7. **Should memory be shared between GUI and CLI sessions?**
   - **Current design:** Both use same service instances and JSON files
   - **Answer:** YES—if you run CLI in one terminal and GUI in another, they see the same memory
   - **Implication:** No duplication of storage; memory is consistent across invocations

### 8. **What happens if user closes GUI without exiting menu?**
   - **Assumed behavior:** Close button closes window and exits cleanly
   - **Implication:** No confirmation dialog needed; closing window = exiting

---

## Scope Signals

### Explicitly IN Scope
- ✅ Add tkinter-based GUI
- ✅ Implement all 14 operations (8 standard + 6 scientific)
- ✅ Display calculation results and errors
- ✅ Show memory entries from `MemoryService`
- ✅ Display statistics from `MemoryService.compute_statistics()`
- ✅ Support mode switching (Standard vs Scientific)
- ✅ Integrate with existing services (no duplication)
- ✅ Provide CLI entry point (`--gui` flag or similar)
- ✅ Error handling (invalid inputs, domain errors)

### Explicitly OUT of Scope
- ❌ No new operations added
- ❌ No changes to storage format
- ❌ No GUI-only features that break CLI compatibility
- ❌ No complex equation parsing or expression trees
- ❌ No database migration
- ❌ No network/cloud features
- ❌ No custom theming or styling (unless very simple)

### Borderline (Clarify for Implementation)
- ? Export/Import buttons in GUI — could add, not Must
- ? Filtering UI in GUI memory panel — could add, not Must
- ? Keyboard shortcuts — could add, not Must
- ? Clearing memory entries — could add, nice to have

---

## Files Affected

### New Files to Create

| File | Purpose | Lines |
|------|---------|-------|
| `src/gui/__init__.py` | Package marker | 5-10 |
| `src/gui/calculator_gui.py` | Main GUI class, window setup, event handlers | 300-500 |

### Files to Modify

| File | Change | Reason |
|------|--------|--------|
| `src/__main__.py` | Add `--gui` flag to argparse; handle GUI invocation | Launch GUI from CLI |
| `src/cli/calculator_cli.py` | Optional: add menu option "Launch GUI" | Backward-compat feature (could skip) |

### No Changes to

| Category | Files |
|----------|-------|
| Models | `src/models/*.py` |
| Services | `src/services/*.py` |
| Storage | `src/storage/*.py` |
| Protocols | `src/protocols/*.py` |
| Tests | `tests/` (existing tests unchanged; GUI not tested in pytest) |

---

## Testing Considerations

### What NOT to Test
- GUI presentation logic (buttons rendering, widget layout) — not testable in unit tests
- Tkinter event loop behavior — framework responsibility
- User input validation at widget level — integration tests only

### What CAN Be Tested (Outside GUI)
- Service method calls and return values — already tested (433 tests)
- Error handling (ValueError propagation) — already tested
- MemoryEntry creation and storage — already tested
- Statistics computation — already tested

### GUI Testing Strategy (If Needed Later)
- Use tkinter testing library (e.g., `pytest-tkinter` or manual fixtures)
- Mock `CalculatorService` and `MemoryService` with stubs
- Verify button clicks trigger correct service calls
- Verify display updates after operations

**For this task:** No new tests required. GUI is a presentation layer over tested services.

---

## Implementation Priority (For Programmer)

1. **Highest:** Create `CalculatorGUI` class with initialization and window setup
2. **High:** Standard mode tab with 8 operation buttons and input/output fields
3. **High:** Scientific mode tab with 6 operation buttons
4. **High:** Calculate button handler to execute operations and handle errors
5. **High:** Memory display panel (read from `MemoryService.retrieve_all()`)
6. **Medium:** Statistics panel (display from `MemoryService.compute_statistics()`)
7. **Medium:** Refresh logic to update memory and stats after each calculation
8. **Medium:** Modify `__main__.py` to add `--gui` flag and invoke GUI
9. **Low:** Export/Import buttons (if time permits)
10. **Low:** Filtering UI (if time permits)

---

## Success Criteria for Task 10

### Must-Have Criteria (Verification Steps)

1. ✅ **GUI window launches**
   - `python -m src --gui` opens a tkinter window without errors

2. ✅ **All 14 operations accessible**
   - Standard mode: Add, Subtract, Multiply, Divide, Square, Square Root, Power, Modulo
   - Scientific mode: Sin, Cos, Tan, Log, Ln, Exp
   - All produce correct results matching CLI behavior

3. ✅ **Error handling**
   - Division by zero: displays user-friendly error message
   - Negative sqrt: displays error
   - Log/Ln of non-positive: displays error
   - Invalid numeric input: displays error (e.g., non-numeric in field)

4. ✅ **Memory integration**
   - Each successful calculation creates a `MemoryEntry` via `memory_service.store()`
   - Memory display shows all entries with operation, operands, result, timestamp
   - Memory display updates after new calculation

5. ✅ **Statistics display**
   - Shows total calculations, error count, error %, execution times
   - Updates after new calculation

6. ✅ **Mode switching**
   - User can switch between Standard and Scientific
   - Operations in each mode are correct

7. ✅ **Existing CLI unchanged**
   - `python -m src` still launches interactive menu
   - `python -m src --operation add 3 5` still works
   - All 433 tests still pass

8. ✅ **Shared memory across sessions**
   - Run GUI, perform calculation, close GUI
   - Run CLI `--memory` flag
   - See the calculation recorded in memory

### Should-Have Criteria (Quality)

1. ✅ Service integration is seamless (no duplication of logic)
2. ✅ Error messages are clear and user-friendly
3. ✅ UI layout is professional and intuitive
4. ✅ Window is reasonably sized (not too small, not huge)
5. ✅ Response time is immediate (< 100ms for calculations)

### Could-Have Criteria (Nice-to-Have)

1. ⏳ Export/Import buttons in GUI
2. ⏳ Memory filtering in GUI
3. ⏳ Keyboard shortcuts
4. ⏳ Dark mode option

---

## Key Design Patterns to Use

### 1. **Separation of Concerns**
- `CalculatorGUI` handles presentation only (tkinter widgets, event routing)
- All calculation logic delegated to services
- All persistence delegated to `MemoryService`

### 2. **Dependency Injection**
- GUI constructor accepts `service: CalculationService` and `memory_service: MemoryService` as parameters
- Enables testing with mocks; enables sharing instances across CLI and GUI

### 3. **Event-Driven Architecture**
- Operation buttons have click handlers that trigger calculations
- Calculation results trigger updates to memory and statistics displays
- Window close button triggers cleanup and exit

### 4. **Model-View Separation**
- Models (`Operation`, `MemoryEntry`, `CalculationStatistics`) are data-only
- Views (GUI widgets) display models without modifying them
- Services are controllers that coordinate models and views

---

## Code Stubs (Template for Programmer)

### `src/gui/__init__.py`
```python
"""
GUI module for OOP Calculator.
Provides tkinter-based graphical interface as alternative to CLI.
"""

from .calculator_gui import CalculatorGUI

__all__ = ["CalculatorGUI"]
```

### `src/gui/calculator_gui.py` (Stub)
```python
import tkinter as tk
from tkinter import ttk, messagebox
from src.models import Operation
from src.models.memory_entry import MemoryEntry
from src.protocols import CalculationService, MemoryService


class CalculatorGUI(tk.Tk):
    """
    Main GUI window for the calculator.
    
    Provides tabs for Standard and Scientific modes, input fields for operands,
    buttons for operations, and displays for memory entries and statistics.
    """
    
    def __init__(self, service: CalculationService, memory_service: MemoryService | None = None):
        super().__init__()
        self.title("OOP Calculator - GUI")
        self.geometry("700x600")
        
        self.service = service
        self.memory_service = memory_service
        
        self._create_widgets()
        self._refresh_memory_display()
        self._refresh_statistics_display()
    
    def _create_widgets(self) -> None:
        """Create and layout all GUI widgets."""
        # TODO: Create notebook (tabs)
        # TODO: Create standard mode tab
        # TODO: Create scientific mode tab
        # TODO: Create input fields for operands
        # TODO: Create result display
        # TODO: Create memory display
        # TODO: Create statistics display
        # TODO: Create buttons (Calculate, Clear, Export, Import, Exit)
        pass
    
    def _create_standard_mode_tab(self) -> tk.Frame:
        """Create tab for standard operations."""
        # TODO: Create 8 operation buttons
        # Return frame
        pass
    
    def _create_scientific_mode_tab(self) -> tk.Frame:
        """Create tab for scientific operations."""
        # TODO: Create 6 operation buttons
        # Return frame
        pass
    
    def _on_operation_button_click(self, operation: Operation) -> None:
        """Handle operation button click."""
        # TODO: Get operands from input fields
        # TODO: Call service.perform(operation, a, b)
        # TODO: Handle success/error
        # TODO: Refresh memory and statistics
        pass
    
    def _execute_calculation(self, operation: Operation, a: float, b: float) -> None:
        """Execute a calculation and record to memory."""
        try:
            result = self.service.perform(operation, a, b)
            self._display_result(result)
            
            # Record to memory
            if self.memory_service:
                entry = MemoryEntry(
                    operation=operation.value,
                    operand_a=a,
                    operand_b=b,
                    result=result.result,
                    success=True,
                    error_message=None,
                    execution_timestamp="",
                    execution_time_ms=result.execution_time_ms,
                    memory_entry_id=None
                )
                self.memory_service.store(entry)
            
            self._refresh_memory_display()
            self._refresh_statistics_display()
        
        except ValueError as e:
            self._show_error(str(e))
    
    def _display_result(self, result) -> None:
        """Display calculation result."""
        # TODO: Update result label/text widget
        pass
    
    def _refresh_memory_display(self) -> None:
        """Refresh memory entries list."""
        if not self.memory_service:
            return
        # TODO: Get all entries via memory_service.retrieve_all()
        # TODO: Update memory list widget
        pass
    
    def _refresh_statistics_display(self) -> None:
        """Refresh statistics display."""
        if not self.memory_service:
            return
        # TODO: Get stats via memory_service.compute_statistics()
        # TODO: Update statistics widget
        pass
    
    def _show_error(self, message: str) -> None:
        """Display error dialog."""
        messagebox.showerror("Calculation Error", message)
    
    def run(self) -> None:
        """Start the GUI event loop."""
        self.mainloop()
```

### `src/__main__.py` (Modifications)
```python
# Add import
from .gui.calculator_gui import CalculatorGUI

def main() -> None:
    parser = argparse.ArgumentParser(...)
    
    # Add new flag
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch graphical user interface (GUI) instead of CLI"
    )
    
    args = parser.parse_args()
    
    # Check if GUI flag is set
    if args.gui:
        service = _build_service()
        memory_service = _build_memory_service()
        gui = CalculatorGUI(service, memory_service)
        gui.run()
        return
    
    # ... rest of existing CLI code
```

---

## Summary: What Needs to Be Built

### New Components
1. **`CalculatorGUI` class** in `src/gui/calculator_gui.py`
   - Inherits from `tk.Tk`
   - Constructor takes `CalculationService` and optional `MemoryService`
   - Creates tabs for Standard and Scientific modes
   - Manages input fields, buttons, result display, memory list, statistics
   - Event handlers for operations, calculations, UI updates

2. **GUI package** at `src/gui/`
   - `__init__.py` to export `CalculatorGUI`
   - `calculator_gui.py` with full implementation

### Modified Components
1. **`src/__main__.py`**
   - Add `--gui` argparse flag
   - Instantiate and run `CalculatorGUI` if flag is set
   - Pass service instances to GUI

### Unchanged
- All existing services, models, storage, CLI
- All 433 tests continue to pass
- JSON file formats

---

## Next Steps for System Architect & Python Programmer

1. **System Architect:** Review this analysis; define exact GUI layout (Option A, B, or C)
2. **Python Programmer:** Create `CalculatorGUI` class following the stub template
3. **Python Programmer:** Wire `--gui` flag in `__main__.py`
4. **Python Programmer:** Implement event handlers and refresh logic
5. **UML Designer:** Update diagrams to show GUI component
6. **Tester:** Run `python -m src --gui` and verify functionality; all 433 tests still pass

