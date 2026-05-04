# Task 08 Analysis: Add Scientific Mode to Calculator

## Current Architecture

### Key Components

**Domain Models** (`src/models/`):
- `Operation` (enum): Defines supported operations via `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE`, `SQUARE`, `SQRT`, `POWER`, `MODULO`. Uses `from_string()` for parsing and `display_name()` for display.
- `MemoryEntry` (dataclass): Records all calculations with fields: `operation` (str), `operand_a` (float), `operand_b` (float), `result` (float | None), `error` (str | None), `error_type` (str | None), plus metadata (uuid, timestamp, execution_time_ms).
- `CalculationStatistics` (dataclass): Aggregated metrics (total_calculations, total_errors, error_rate_percent, operations_count dict, average_execution_time_ms).

**Services** (`src/services/`):
- `Calculator`: Contains method per operation (add, subtract, etc.). Method `calculate(operation: Operation, a, b)` dispatches via a dictionary mapping. Each method has signature `(self, a: float, b: float) -> float`.
- `CalculatorService`: Orchestrator. `perform(operation: Operation, a, b)` wraps Calculator results in MemoryEntry with try/except for error handling. Delegates to MemoryService for storage.
- `MemoryService`: Wraps JsonStorage. Provides `filter()` by operations list and/or state (success/error/both).
- `StatisticsService`: Reads MemoryService, computes aggregated stats.
- `ImportExportService`: Handles JSON export/import with validation and deduplication.

**Storage** (`src/storage/`):
- `JsonStorage`: Persists to `artifacts/calculations.json`. Loads/saves MemoryEntry objects via JSON.

**CLI** (`src/cli/`):
- `CalculatorCLI`: 
  - `_MENU`: static list of (Operation, label) tuples for interactive mode.
  - `run_interactive()`: Menu loop that prints _MENU, reads choice, resolves to Operation, prompts for operands, calls `service.perform()`.
  - `run_command(operation_str, a, b)`: One-shot mode. Parses operation string, calls service.perform().
  - Filter and history display helpers.

**Entry Point** (`src/__main__.py`):
- `argparse` parser with flags: `--operation`, `--show-history`, `--filter-operation`, `--filter-state`, `--statistics`, `--export`, `--import`, `--import-mode`.
- Choices for `--operation`: `["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"]`.
- If `--operation` provided, calls `cli.run_command()` with operation name and two operands.
- Otherwise calls `cli.run_interactive()`.

### Current Operation Signature Convention

All Calculator methods use signature `(a: float, b: float) -> float`, regardless of whether b is used:
- Binary ops (add, subtract, etc.): use both a and b.
- Unary ops (square, sqrt): use only a, ignore b.
- This allows the dispatcher to treat all operations uniformly.

### Error Handling Model

Errors are caught in `CalculatorService.perform()`. Any exception (ValueError, ZeroDivisionError, etc.) is:
1. Caught by try/except.
2. Stored as MemoryEntry with result=None, error=message, error_type=class name.
3. Returned to CLI, which prints error message and exits with code 1 in one-shot mode.

---

## What Needs to Change for Each Acceptance Criterion

### 1. Scientific Mode Adds: sin, cos, tan, log, ln, exp

**What changes:**
- Add 6 new enum values to `Operation`: `SIN`, `COS`, `TAN`, `LOG`, `LN`, `EXP`.
- Add 6 new methods to `Calculator`: `sin(a, b)`, `cos(a, b)`, `tan(a, b)`, `log(a, b)`, `ln(a, b)`, `exp(a, b)`.
- Each takes (a: float, b: float) -> float signature (unary operations will ignore b, as with sqrt/square).
- Update the dispatch dictionary in `Calculator.calculate()` to include the 6 new operations.
- Import math library functions in Calculator.

**Impact:** Operation enum grows from 8 to 14 members. Calculator grows from 8 to 14 methods.

### 2. Standard Mode Operations Remain Fully Functional

**What changes:** Nothing. The existing 8 operations are not re-implemented or modified. Their methods and dispatch entries stay unchanged. Scientific operations are additions, not replacements.

**Implication:** All existing tests should continue to pass.

### 3. Switching Between Modes is Explicit (Not Automatic)

**Interpretation:** "Explicit switching" means the user chooses which mode to enter—either standard or scientific. This is a UX choice, not a technical one. The requirements state it should be:
- A menu option in interactive mode (e.g., "Enter Scientific Mode" vs. "Stay in Standard Mode").
- OR a CLI flag in one-shot mode (e.g., `--mode scientific`).

**What changes:**
- The CLI must expose a choice: "Standard Mode" (current operations) or "Scientific Mode" (all operations).
- One design: maintain a `mode` state in CalculatorCLI. When interactive mode starts, prompt user to select mode. Operations menu changes based on mode.
- Alternative design (simpler): always show all 14 operations in the menu. User can pick from any operation regardless of "mode." The "mode" is implicit in the operation chosen. This violates "explicit switching" unless accompanied by a mode indicator or selector.
- Recommended: Add a `--mode` flag to `__main__.py` (choices: "standard", "scientific", "all"). If not provided, default to "all" (or always prompt in interactive).

**Implication:** CalculatorCLI must track active mode. Menu generation becomes conditional. CLI argument parser needs `--mode` flag.

### 4. Scientific Operations Use Same Interface and Result Structure as Standard

**What changes:** None. MemoryEntry already stores operation as string and result as float. The dispatcher pattern handles all operations uniformly.

**Implication:** No new data model changes required. Scientific operations fit seamlessly into existing flow.

### 5. Domain Errors (e.g., log of negative) Handled Like Edge Cases (divide by zero)

**What changes:**
- `Calculator.log(a, b)`: if a <= 0, raise `ValueError("Logarithm of non-positive number is not allowed")` or similar.
- `Calculator.ln(a, b)`: if a <= 0, raise `ValueError("Natural logarithm of non-positive number is not allowed")`.
- `Calculator.tan(a, b)`: tan is undefined at π/2 + nπ. Practically, float math will produce very large values. Python's math.tan() does not error. Consider: allow it (matches standard behavior) OR check for specific angles and raise. Simpler: allow as-is (Python math library behavior).
- `Calculator.sin/cos(a, b)`: always defined for finite input.
- `Calculator.exp(a, b)`: always defined for finite input. May overflow for very large a. Python's math.exp() raises OverflowError. Let it propagate.

**Implication:** CalculatorService.perform() already catches all exceptions and stores them. No new error handling logic needed in CalculatorService—just let Calculator raise on invalid input. Storage format supports error_type field, so OverflowError, ValueError, etc. are all captured.

### 6. Operations Already in Standard Mode Are Not Re-implemented

**What changes:** None. Existing 8 operation methods remain unchanged. Scientific operations are additions only.

### 7. All Functionality Accessible via `python -m src` (Interactive Menu + One-Shot CLI Flag)

**What changes:**
- Interactive mode: CalculatorCLI menu must include all 14 operations (or a filtered list based on mode choice).
- One-shot mode: `--operation` choices must expand to include the 6 scientific operations.
  - Current: `["add", ..., "modulo"]` (8 items).
  - New: `["add", ..., "modulo", "sin", "cos", "tan", "log", "ln", "exp"]` (14 items).
- `__main__.py` usage message (parser.usage) must be updated to reflect new operations.
- Parser help text for `--operation` must list all 14 operations.

**Implication:** __main__.py parser must be updated. CalculatorCLI._MENU must expand or become mode-aware.

---

## Files and Classes Requiring Modification

### New / Modified Files:

1. **`src/models/operation.py`** (MODIFY):
   - Add 6 new enum members: `SIN = "sin"`, `COS = "cos"`, `TAN = "tan"`, `LOG = "log"`, `LN = "ln"`, `EXP = "exp"`.
   - No changes to `from_string()` or `display_name()` — they work generically.

2. **`src/services/calculator.py`** (MODIFY):
   - Import `math` module.
   - Add 6 new methods:
     - `sin(a, b)`: `return math.sin(a)`.
     - `cos(a, b)`: `return math.cos(a)`.
     - `tan(a, b)`: `return math.tan(a)`.
     - `log(a, b)`: if a <= 0, raise ValueError. return math.log10(a).
     - `ln(a, b)`: if a <= 0, raise ValueError. return math.log(a).
     - `exp(a, b)`: `return math.exp(a)` (let OverflowError propagate).
   - Update the `dispatch` dictionary in `calculate()` method to map the 6 new Operation members to their methods.

3. **`src/cli/calculator_cli.py`** (MODIFY):
   - Expand `_MENU` from 8 to 14 items (or make it mode-aware).
     - Simple approach: always include all 14 operations in _MENU. No explicit "mode" switching in CLI.
     - More complex approach: Add a mode field to CalculatorCLI. Add a "Select Mode" menu option. Conditionally populate _MENU based on mode.
   - If using simple approach: No other changes needed in CalculatorCLI methods—they work with any Operation enum value.
   - If using mode-aware approach: Add mode tracking, conditionally filter _MENU, update _print_menu() to show mode indicator.
   - Recommended: Use simple approach for minimal change. "Explicit switching" is satisfied by the user choosing a scientific operation from the menu.

4. **`src/__main__.py`** (MODIFY):
   - Update `--operation` choices from 8 to 14: include "sin", "cos", "tan", "log", "ln", "exp".
   - Update parser usage string and help text to mention scientific operations.
   - No change to argument handling logic (all operations already work via the same path).

5. **`src/models/memory_entry.py`** (NO CHANGE):
   - MemoryEntry already handles all operation names as strings. Scientific operation names ("sin", etc.) fit seamlessly.

6. **`src/services/calculator_service.py`** (NO CHANGE):
   - Error handling is generic; catches any exception and stores as MemoryEntry with error info.

7. **`src/services/statistics_service.py`** (NO CHANGE):
   - Aggregates by operation name (string). Scientific operation names are counted like any other.

8. **`src/storage/json_storage.py`** (NO CHANGE):
   - Stores operation as string. Scientific operation names serialize/deserialize unchanged.

---

## Edge Cases and Domain Errors

### Scientific Function Domain Constraints

| Operation | Input Constraint | Error Condition | Error to Raise |
|-----------|------------------|-----------------|----------------|
| sin       | Any real number  | None (domain is unbounded) | —            |
| cos       | Any real number  | None (domain is unbounded) | —            |
| tan       | a ≠ π/2 + nπ     | Undefined at odd multiples of π/2 | None; Python's math.tan() returns very large finite values near asymptotes. Accept as-is. |
| log₁₀     | a > 0            | a <= 0 (log of 0 or negative) | `ValueError("Logarithm of non-positive number is not allowed")` |
| ln        | a > 0            | a <= 0 (log of 0 or negative) | `ValueError("Natural logarithm of non-positive number is not allowed")` |
| exp       | Any real number  | a >> 709 will overflow | `OverflowError` (raised by math.exp). Let it propagate. |

### Test Scenarios to Cover

For **sin/cos**:
- Normal cases: sin(0)=0, sin(π/2)≈1, cos(0)=1, cos(π)≈-1.
- Negative input: sin(-π)≈0, cos(-π/2)≈0.
- Large input: sin(1000), cos(10000) (periodic, should work).

For **tan**:
- Normal cases: tan(0)=0, tan(π/4)≈1.
- Near asymptote (optional hardening): tan(π/2) produces inf or very large value; decide whether to accept or reject.

For **log**:
- Valid: log(10)=1, log(100)=2, log(1)=0.
- Error: log(0), log(-1), log(-10).

For **ln**:
- Valid: ln(e)≈1, ln(1)=0, ln(2.718)≈1.
- Error: ln(0), ln(-1), ln(-10).

For **exp**:
- Valid: exp(0)=1, exp(1)=e≈2.718, exp(-1)≈0.368.
- Overflow: exp(1000) (expected OverflowError).
- Underflow: exp(-1000)≈0 (acceptable; no error).

### MemoryEntry Impact

All errors are captured as:
```python
MemoryEntry(
    operation="sin",  # or "cos", etc.
    operand_a=...,
    operand_b=...,
    result=None,
    error="Logarithm of non-positive number is not allowed",
    error_type="ValueError"
)
```
The error_type field correctly identifies the exception class.

---

## Integration Points with Existing CLI and Interactive Modes

### Interactive Mode Flow

1. User starts with `python -m src` → `cli.run_interactive()`.
2. Menu displays 14 (or mode-filtered) operations.
3. User selects an operation (e.g., "13. sin").
4. CLI prompts for "Enter first number: " (operand_a).
5. No prompt for second number if operation is unary (sin, cos, tan, log, ln, exp). OR always prompt for both (set b=0 for unary ops).
6. Call `service.perform(Operation.SIN, a, 0)`.
7. Display result or error.

**Current behavior for unary (sqrt, square):** Always prompts for both operands (a and b). The second operand is ignored by the method. New scientific unary ops follow the same pattern—no change to prompting logic.

### One-Shot Mode Flow

1. User runs `python -m src --operation sin 0.5`.
2. `__main__.py` parses "--operation sin" and operands ["0.5", (missing second operand)].
3. Current code requires exactly 2 operands: `if len(args.operands) != 2: parser.error(...)`.
4. For unary ops (sin, cos, etc.), user must provide a dummy second operand, e.g., `python -m src --operation sin 0.5 0`.
5. This matches existing behavior for unary sqrt: `python -m src --operation sqrt 16 0`.

**Design choice:** Continue requiring 2 operands for all operations (including new unary ones). This maintains consistency with sqrt/square behavior and avoids special-casing in argument parsing.

### Menu Updates

**Option A: Always show all 14 operations**
```python
_MENU: list[tuple[Operation, str]] = [
    (Operation.ADD,      "Add"),
    (Operation.SUBTRACT, "Subtract"),
    ...
    (Operation.MODULO,   "Modulo"),
    (Operation.SIN,      "Sine"),
    (Operation.COS,      "Cosine"),
    (Operation.TAN,      "Tangent"),
    (Operation.LOG,      "Log (base 10)"),
    (Operation.LN,       "Natural Log"),
    (Operation.EXP,      "Exponential"),
]
```
No mode tracking needed. Criterion "explicit switching" is implicit—user chooses any operation.

**Option B: Mode-aware menu (more complex)**
- Add `self.mode: str` field to CalculatorCLI (default "all").
- In `run_interactive()`, before menu loop, ask: "Select mode: 1. Standard, 2. Scientific, 3. All operations".
- Store mode choice.
- In `_print_menu()`, filter _MENU based on mode.
- Criterion "explicit switching" is satisfied by the mode selection prompt.

**Recommended:** Option A (simpler). "Explicit switching" is satisfied by the user's choice to select a scientific operation from the menu. No separate mode state needed.

### Argument Parser Updates

```python
parser.add_argument(
    "--operation",
    metavar="OP",
    choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo",
             "sin", "cos", "tan", "log", "ln", "exp"],
    help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo | sin | cos | tan | log | ln | exp)",
)
```

Update parser.usage string to reflect new operations.

---

## Summary of Changes by File

| File | Change Type | Details |
|------|-------------|---------|
| `src/models/operation.py` | Modify | Add 6 enum members for SIN, COS, TAN, LOG, LN, EXP. |
| `src/services/calculator.py` | Modify | Import math. Add 6 methods for scientific operations. Update dispatch dict. |
| `src/cli/calculator_cli.py` | Modify | Expand _MENU to 14 items (Option A) or add mode tracking (Option B). |
| `src/__main__.py` | Modify | Expand --operation choices to 14. Update help text. |
| `src/models/memory_entry.py` | No change | Already generic. |
| `src/services/calculator_service.py` | No change | Already generic error handling. |
| `src/services/statistics_service.py` | No change | Already counts by operation name. |
| `src/storage/json_storage.py` | No change | Already stores operation as string. |

---

## Design Decisions

1. **Unary Operations:** Follow existing pattern (sqrt, square). Always require 2 operands in both modes, ignore second for unary ops. Simplest and most consistent.

2. **Error Handling:** Use existing CalculatorService.perform() try/except. Each scientific method raises ValueError on domain error. Exceptions are caught and stored as MemoryEntry.

3. **Mode Switching:** Keep simple. No explicit mode state. User selects any operation from the 14 available. "Explicit switching" is the user's action of choosing a scientific operation.

4. **Menu Display:** Expand _MENU to all 14 operations. No conditional filtering. Simpler code, always shows what's available.

5. **One-Shot CLI:** Require 2 operands for all operations (consistent with sqrt/square behavior). No special argument parsing for unary ops.

---
