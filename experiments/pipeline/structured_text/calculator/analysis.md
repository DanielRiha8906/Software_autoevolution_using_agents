# Calculator Scientific Mode — Analysis Report

**Date:** 2026-05-03  
**Working Directory:** `/experiments/pipeline/structured_text/calculator/`  
**Task:** Add scientific mode with sin, cos, tan, log (base 10), ln (natural log), and exp operations

## Executive Summary

The calculator project is a well-structured OOP Python application with layered architecture (models, services, storage, CLI). Adding scientific mode requires minimal architectural changes: extend the Operation enum, add corresponding methods to Calculator, update the CLI menu system, and expose new operations via CLI flags. The design supports explicit mode switching through a menu option or implicit switching when scientific operations are selected.

---

## Current Architecture Overview

### Layered Design

1. **Models Layer** (`src/models/`)
   - `operation.py`: Operation enum with factory methods
   - `calculation_result.py`: Result dataclass with symbol mapping
   - `memory_entry.py`: Audit trail dataclass
   - `calculation_statistics.py`: Statistics computation

2. **Services Layer** (`src/services/`)
   - `calculator.py`: Pure arithmetic logic (8 operations)
   - `calculator_service.py`: Orchestrates Calculator + persists via JsonStorage
   - `memory_service.py`: Memory queries, filters, statistics, import/export

3. **Storage Layer** (`src/storage/`)
   - `json_storage.py`: Persists CalculationResult
   - `memory_json_storage.py`: Persists MemoryEntry

4. **CLI Layer** (`src/cli/`)
   - `calculator_cli.py`: Interactive menu (16 options: 8 operations + 8 admin) and one-shot mode

5. **Entry Point**
   - `src/__main__.py`: Argument parser, service instantiation, delegation to CLI

### Data Flow

```
argparse → CalculatorCLI → CalculatorService → Calculator → (math)
                        ↓
                   JsonStorage (history)
                   MemoryService (audit)
```

### Current Operations (8 total)

All take two operands (a, b):
- **Binary:** add, subtract, multiply, divide, power, modulo
- **Unary (ignores b):** square, sqrt

All results persisted to `artifacts/calculations.json` and `artifacts/memory_entries.json`.

### CLI Menu Structure

Interactive mode shows 16 options:
1. Add (operation 1)
2. Subtract (operation 2)
...
8. Modulo (operation 8)
9. View history
10. View memory
11. Filter by operation
12. Filter by status
13. View statistics
14. Export to file
15. Import from file
16. Exit

Menu calculations: `len(_MENU) + N` where `_MENU` has 8 entries, admin options start at 9.

---

## What Operations Are Implemented and How

### Operation Enum (`src/models/operation.py`)
```python
class Operation(Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    # ... (8 members)
```
- Each operation maps string name to enum member
- `from_string()` factory resolves CLI args to enum
- `display_name()` returns capitalized label for menu

### Calculator Class (`src/services/calculator.py`)
- 8 methods: `add()`, `subtract()`, `multiply()`, `divide()`, `square()`, `sqrt()`, `power()`, `modulo()`
- All have signature `func(a: float, b: float) -> float`
- Some methods ignore `b` (unary ops like square, sqrt)
- Validation: division by zero, sqrt of negative → ValueError
- Dispatch via `calculate(operation: Operation, a: float, b: float)` method

### CalculationResult (`src/models/calculation_result.py`)
- Stores operation as string: `"add"`, `"sqrt"`, etc.
- Renders via `_SYMBOLS` dict: maps operation string to Unicode symbol
- For unary ops (square, sqrt), both operands stored even though b ignored

### CalculatorCLI (`src/cli/calculator_cli.py`)
- `_MENU` tuple list: `[(Operation.ADD, "Add"), ...]` — order matters for menu indexing
- Interactive: loops until exit, resolves menu choice → Operation enum → prompts numbers → calls `service.perform()`
- One-shot: `run_command(op_string, a, b)` converts op_string → Operation enum → same path
- Memory filtering by operation name uses string comparison: `filter_by_operation("add")`

### MemoryEntry (`src/models/memory_entry.py`)
- Stores `operation: str` — operation name as string, not enum
- Backward compatible: handles old `timestamp` field
- Filter queries match on `operation` field string directly

---

## Which Classes/Modules Need Modification

### 1. `src/models/operation.py` — MUST MODIFY
- Add 6 new enum members: SIN, COS, TAN, LOG, LN, EXP
- All new operations need `from_string()` to recognize them
- `display_name()` already handles all enums generically via `.value.capitalize()`

### 2. `src/services/calculator.py` — MUST MODIFY
- Add 6 new methods: `sin()`, `cos()`, `tan()`, `log()`, `ln()`, `exp()`
- Decide operand signature:
  - **Unary scientific ops** (sin, cos, tan, log, ln, exp) ignore `b` parameter, only use `a`
  - Match existing unary pattern (square, sqrt) for consistency
- Add imports: `import math` (already imported)
- Update `calculate()` dispatch dict with new operations
- Error handling: domain validation (e.g., log/ln of non-positive)

### 3. `src/cli/calculator_cli.py` — MUST MODIFY
- Extend `_MENU` tuple list with 6 new operations: `(Operation.SIN, "Sin"), ...`
- Menu numbering auto-adjusts via `len(_MENU)`, so option numbers shift
- Update hardcoded prompts if any mention operation list (e.g., in filter prompt at line 241)
- New menu will have 14 operations + 8 admin = 22 total options

### 4. `src/__main__.py` — MUST MODIFY
- Extend `--operation` argument choices to include: `["add", ..., "sin", "cos", "tan", "log", "ln", "exp"]`
- Update help text / usage string to reflect new operations
- Update argparse `--filter-operation` help text to list all operations
- No logic change: `Operation.from_string()` already handles new members

### 5. `src/models/calculation_result.py` — CONDITIONAL MODIFY
- Add symbol mappings for new operations to `_SYMBOLS` dict:
  - `"sin": "sin"`, `"cos": "cos"`, etc. (or use Unicode if preferred)
  - Unary ops (square: `²`, sqrt: `√`, power: `^`) have special symbols
  - Scientific ops commonly use their function names
- If new operations are truly unary (ignore b), check if `__str__()` needs adjustment
  - Current code: `f"{a} {symbol} {b} = {r}"` works for binary
  - For unary: renders as "5 sin 0 = 0.959..." (confusing because b is shown)
  - Consider: format unary ops differently, e.g., `"sin(5) = 0.959..."`

### 6. Tests — MUST ADD
- `test_calculator.py`: Add test methods for each new operation (sin, cos, tan, log, ln, exp)
  - Test valid domains, boundary cases, error cases
  - Test dispatch via `calculate()` method
- `test_cli.py`: Add interactive menu tests for new operations (test indices 9-14)
  - Update exit test index (currently 16, will be 22)
  - Test new menu items trigger correct operations
- `test_cli_flags.py`: Add one-shot CLI tests for each new operation
  - Test `python -m src --operation sin 1` etc.
  - Test invalid inputs (negative log, etc.)
- No changes needed to storage, service integration tests — operations are transparent to them

---

## How Mode Switching Should Be Implemented

### Option 1: Implicit Mode Switching (Recommended for simplicity)
- **No explicit mode toggle** — the menu naturally shows all 14 operations
- User sees operations 1-8 (standard) and 9-14 (scientific) in same menu
- Selecting operation 1-8 uses standard mode; selecting 9-14 uses scientific mode
- **Advantage:** Minimal code change, matches existing architecture, no state to manage
- **Implementation:** Just add operations to enum and menu

### Option 2: Explicit Mode Switching (If mode separation required)
- Add a "mode" field to Calculator or CalculatorService to track state
- New menu option: "Switch to Scientific Mode" (or vice versa)
- Show different operation subsets based on mode
- Requires maintaining mode state across interactive loop
- **Disadvantage:** More complex, breaks symmetry of current design, adds state management

### Recommended Approach: Implicit + Optional Menu Split
- **Primary (Implicit):** Single menu with all 14 operations
- **Optional Enhancement:** Add visual grouping in menu output:
  ```
  === Standard Operations ===
  1. Add
  ...
  8. Modulo
  
  === Scientific Operations ===
  9. Sin
  ...
  14. Exp
  
  === Other ===
  15. View history
  ...
  22. Exit
  ```
- No functional mode switching, just organizational UX

---

## Summary of All Required Changes

### Files to Modify

#### 1. `/src/models/operation.py`
- Add 6 enum members: SIN, COS, TAN, LOG, LN, EXP
- No other changes needed (from_string and display_name already generic)

#### 2. `/src/services/calculator.py`
- Add 6 methods: sin(a, b), cos(a, b), tan(a, b), log(a, b), ln(a, b), exp(a, b)
- Update `calculate()` dispatch dict: add 6 new mappings
- Error handling: check domain validity (e.g., log(a) requires a > 0)
- All use `import math` (already present)

#### 3. `/src/models/calculation_result.py`
- Extend `_SYMBOLS` dict with 6 new entries (e.g., `"sin": "sin"`)
- Optionally refactor `__str__()` for better unary operation formatting

#### 4. `/src/cli/calculator_cli.py`
- Extend `_MENU` tuple list with 6 new (Operation, label) pairs
- Update hardcoded operation list in filter prompt (line 241) if needed
- Consider adding section header comments to clarify standard vs. scientific

#### 5. `/src/__main__.py`
- Extend `--operation` choices: add `"sin", "cos", "tan", "log", "ln", "exp"`
- Update argparse usage/help strings
- Update --filter-operation help to list all operations
- No logic changes required

#### 6. `/tests/` — New Test Coverage
- Extend `test_calculator.py`: Add ~30-40 tests for new operations
- Extend `test_cli.py`: Add ~10 tests for new menu items
- Extend `test_cli_flags.py`: Add ~10 tests for new CLI flags
- Update exit option index tests (16 → 22)

### No Changes Required
- Storage layer: transparent to operation names
- MemoryService: works with string operation names, no enum changes
- JsonStorage: same persistence mechanism
- MemoryEntry: already stores operations as strings
- ServiceIntegration: CalculatorService.perform() handles any Operation enum member

### Files That Benefit From Optional Refactoring
- `/src/models/calculation_result.py`: `__str__()` could format unary operations better
- `/src/cli/calculator_cli.py`: Could add visual section headers to menu

---

## Implementation Constraints & Considerations

### Operand Handling for Scientific Functions
- **Current:** All Calculator methods have signature `(a: float, b: float) -> float`
- **Scientific ops are unary:** sin(x), cos(x), tan(x), log(x), ln(x), exp(x)
- **Solutions:**
  1. **Keep `(a, b)` signature, ignore b:** Matches square(), sqrt() pattern. User prompted for both numbers in interactive mode (second ignored).
  2. **Change signature:** Would require refactoring Calculator dispatch logic.
- **Recommendation:** Option 1 — maintain signature consistency, ignore b for unary.

### Interactive Mode Prompts
- Current: `"Enter first number: "` and `"Enter second number: "`
- For scientific ops (e.g., sin), users enter two numbers but second is ignored
- **Options:**
  1. Keep generic prompts (minimal change, slight UX awkwardness)
  2. Detect operation type and show context-aware prompts
  3. For scientific ops, show only one prompt
- **Recommendation:** Option 1 for simplicity; Option 2 is future enhancement.

### Validation & Error Handling
- **log(x) requires x > 0** — log(0) and log(negative) are undefined
- **ln(x) requires x > 0** — same as log
- **tan(x) undefined at x = π/2 + nπ** — edge case, likely acceptable to let math.tan() return near-infinite values
- **Negative square roots already handled** — pattern is in place
- Strategy: Add domain checks in method, raise ValueError with clear message
- All errors propagate to MemoryEntry as failure records

### Operation Names in Memory
- All stored as strings (e.g., "sin", "cos")
- Backward compatible: MemoryEntry.from_dict() handles string → filter
- Filter queries already work: `filter_by_operation("sin")` ✓

---

## Estimated Scope & Complexity

| Category | Count | Complexity |
|----------|-------|------------|
| Enum members to add | 6 | Trivial |
| Calculator methods to add | 6 | Low (each 2-4 lines) |
| Menu entries to add | 6 | Trivial |
| CLI choices to add | 6 | Trivial |
| Test methods to add | ~50 | Medium (domain coverage) |
| **Total new lines** | ~150-200 | Medium (mostly tests) |
| **Files to modify** | 6 | Low (focused changes) |
| **Risk level** | Low | No refactoring; additive only |

---

## Verification Checklist (for implementer)

- [ ] All 6 scientific operations appear in Operation enum
- [ ] All 6 operations accessible via `Operation.from_string()`
- [ ] All 6 have methods in Calculator class
- [ ] All 6 in Calculator.calculate() dispatch dict
- [ ] All 6 have menu entries in CLI._MENU
- [ ] All 6 added to --operation choices in argparse
- [ ] All 6 have symbol mappings in CalculationResult._SYMBOLS
- [ ] Domain validation in place (log, ln require positive x)
- [ ] Interactive menu works: options 1-14 functional
- [ ] CLI one-shot works: `python -m src --operation sin 0.5` outputs result
- [ ] Tests pass: pytest tests/ -q returns no failures
- [ ] Memory storage works: new operations recorded in memory_entries.json
- [ ] Help text accurate: `python -m src --help` lists all operations

