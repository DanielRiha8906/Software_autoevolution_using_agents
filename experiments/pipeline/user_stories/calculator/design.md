# Task 03 Design Specification: MemoryEntry Implementation

## OVERVIEW

The MemoryEntry class will serve as the canonical history record type, replacing CalculationResult as the primary persistence object while maintaining backward compatibility. Each MemoryEntry will have a UUID, capture both successful calculations and errors, and be persisted through an updated JsonStorage layer.

---

## DATACLASS DEFINITION

### MemoryEntry (`src/models/memory_entry.py`)

**Fields:**
```python
@dataclass
class MemoryEntry:
    operation: str              # e.g., "add", "subtract", "divide"
    operand_a: float            # first operand
    operand_b: float            # second operand
    result: float | None        # None if operation failed
    error: str | None           # error message if operation failed
    error_type: str | None      # exception type name if operation failed
    timestamp: str = field(default_factory=...)  # ISO format datetime
    uuid: str = field(default_factory=...)       # UUID v4
```

**Methods:**

1. `__post_init__()` — Auto-generate uuid (uuid4()) and timestamp (datetime.now().isoformat()) if not provided
2. `to_dict() -> dict` — Return all fields as dictionary for JSON serialization
3. `@classmethod from_dict(cls, data: dict) -> MemoryEntry` — Deserialize from dict with backward compatibility:
   - If uuid missing: generate with uuid4()
   - If error/error_type missing: set to None
4. `__str__() -> str` — Format: "A SYMBOL B = RESULT" for success, "A SYMBOL B = ERROR: message" for error

**Key Detail:** UUID and timestamp are auto-generated on instantiation. For backward compat, from_dict() fills missing fields.

---

## REQUIRED CHANGES

### 1. NEW FILE: `src/models/memory_entry.py`

**Create:** Complete MemoryEntry dataclass with all fields and methods as described above.

**Dependencies:**
```python
from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import uuid4
```

**Symbols dict:** Use existing _SYMBOLS pattern from CalculationResult.

---

### 2. MODIFIED: `src/models/__init__.py`

**Add import:**
```python
from .memory_entry import MemoryEntry
```

**Add to __all__:**
```python
"MemoryEntry"
```

Keep existing CalculationResult import for backward compatibility.

---

### 3. MODIFIED: `src/services/calculator_service.py`

**Import MemoryEntry:**
```python
from models import MemoryEntry
```

**Modify perform() method:**

Replace:
```python
def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
    result = self.calculator.calculate(operation, a, b)
    calc_result = CalculationResult(...)
    self.storage.save(calc_result)
    return calc_result
```

With:
```python
def perform(self, operation: Operation, a: float, b: float) -> MemoryEntry:
    try:
        result = self.calculator.calculate(operation, a, b)
        entry = MemoryEntry(
            operation=operation.value,
            operand_a=a,
            operand_b=b,
            result=result,
            error=None,
            error_type=None
        )
    except Exception as e:
        entry = MemoryEntry(
            operation=operation.value,
            operand_a=a,
            operand_b=b,
            result=None,
            error=str(e),
            error_type=type(e).__name__
        )
    self.storage.save(entry)
    return entry
```

**Modify get_history() method:**

Return type changes from `list[CalculationResult]` to `list[MemoryEntry]` — JsonStorage.load_all() now returns MemoryEntry objects.

**Key Detail:** Service DOES NOT re-raise exceptions. It returns a MemoryEntry with error state set. CLI is responsible for checking error state.

---

### 4. MODIFIED: `src/storage/json_storage.py`

**Import MemoryEntry:**
```python
from models import MemoryEntry
```

**Modify save() method signature:**
```python
def save(self, result: MemoryEntry) -> None:  # was CalculationResult
```

Implementation:
```python
def save(self, result: MemoryEntry) -> None:
    entries = self._read_raw()
    entries.append(result.to_dict())
    self._write_raw(entries)
```

**Modify load_all() method:**
```python
def load_all(self) -> list[MemoryEntry]:  # was list[CalculationResult]
    entries = self._read_raw()
    return [MemoryEntry.from_dict(entry) for entry in entries]
```

**Backward Compatibility:** MemoryEntry.from_dict() handles old CalculationResult format (missing uuid, error, error_type).

---

### 5. MODIFIED: `src/cli/calculator_cli.py`

**Import MemoryEntry:**
```python
from models import MemoryEntry
```

**Modify _show_history() method:**

Iterate through MemoryEntry objects:
```python
def _show_history(self) -> None:
    history = self.service.get_history()
    if not history:
        print("No calculations recorded yet.")
        return
    
    for i, entry in enumerate(history, 1):
        if entry.error:
            print(f"{i}. {entry.operation} ({entry.operand_a}, {entry.operand_b}) = ERROR: {entry.error}")
        else:
            print(f"{i}. {entry}")
```

**Modify run_interactive() method:**

After `result = self.service.perform()`:
```python
result = self.service.perform(operation, a, b)
if result.error:
    print(f"Error: {result.error}")
else:
    print(f"Result: {result}")
```

No exception handling needed anymore (service handles it internally).

**Modify run_command() method:**

After `result = self.service.perform()`:
```python
result = self.service.perform(operation, a, b)
if result.error:
    print(f"Error: {result.error}", file=sys.stderr)
    sys.exit(1)
else:
    print(result)
```

---

### 6. MODIFIED: `src/__main__.py`

**Add import:**
```python
import sys
```

**Add new argument to parser:**
```python
parser.add_argument(
    "--show-history",
    action="store_true",
    help="Display all calculation history"
)
```

**Add logic after parsing args:**
```python
service = _build_service()
cli = CalculatorCLI(service)

if args.show_history:
    cli._show_history()
    sys.exit(0)

if args.operation:
    # existing one-shot mode code
    ...
else:
    cli.run_interactive()
```

**Usage examples:**
```bash
python -m src --show-history
python -m src --operation add 3 5
python -m src
```

---

## DATA FLOW EXAMPLES

### Success Path

1. User: `python -m src --operation add 3 5`
2. CalculatorService.perform(Operation.ADD, 3, 5):
   - Calculator.calculate() returns 8.0
   - MemoryEntry created: (operation="add", operand_a=3, operand_b=5, result=8.0, error=None, error_type=None)
   - JsonStorage.save(entry) → JSON updated
   - Return MemoryEntry with success state
3. CalculatorCLI.run_command():
   - Check result.error → None
   - Print "3 + 5 = 8.0"

### Error Path

1. User: `python -m src --operation divide 5 0`
2. CalculatorService.perform(Operation.DIVIDE, 5, 0):
   - Calculator.calculate() raises ValueError("Division by zero is not allowed")
   - Exception caught
   - MemoryEntry created: (operation="divide", operand_a=5, operand_b=0, result=None, error="Division by zero is not allowed", error_type="ValueError")
   - JsonStorage.save(entry) → JSON updated with error entry
   - Return MemoryEntry with error state
3. CalculatorCLI.run_command():
   - Check result.error → "Division by zero is not allowed"
   - Print to stderr: "Error: Division by zero is not allowed"
   - sys.exit(1)

### History Display

1. User: `python -m src --show-history`
2. CalculatorCLI._show_history():
   - Get history from service
   - For each MemoryEntry:
     - If error: print "i. operation (a, b) = ERROR: {error_message}"
     - If success: print "i. {entry}" (using MemoryEntry.__str__())

---

## BACKWARD COMPATIBILITY

**Old JSON Format (no uuid, error, error_type):**
```json
{
  "operation": "add",
  "operand_a": 3,
  "operand_b": 5,
  "result": 8,
  "timestamp": "2026-05-03T10:00:00.000000"
}
```

**New JSON Format (with uuid, error, error_type):**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "operation": "add",
  "operand_a": 3,
  "operand_b": 5,
  "result": 8,
  "error": null,
  "error_type": null,
  "timestamp": "2026-05-03T10:00:00.000000"
}
```

**Migration:** On load, MemoryEntry.from_dict() fills missing fields (uuid generated, error/error_type set to None). No explicit migration code needed.

---

## TEST COVERAGE

### New Test Files

1. **test_memory_entry.py** — MemoryEntry class tests (serialization, deserialization, UUID, timestamp)
2. **test_calculator_service_with_errors.py** — Error handling in service (catching, recording, returning MemoryEntry)
3. **test_json_storage_migration.py** — Backward compatibility (loading old format, saving new format)
4. **test_cli_show_history_flag.py** — --show-history flag behavior
5. **test_cli_interactive_menu.py** — Error display in interactive mode

### Existing Test Updates

- **test_calculator_service.py** — Update type expectations to MemoryEntry; add error cases
- **test_cli.py** — Update to check MemoryEntry.error state instead of catching exceptions
- **test_json_storage.py** — Update to work with MemoryEntry format

### Key Test Scenarios

1. MemoryEntry creation with auto-generated UUID and timestamp
2. MemoryEntry serialization (success and error states)
3. MemoryEntry deserialization with old format (backward compat)
4. Service capturing and recording errors without re-raising
5. Storage saving both success and error entries
6. CLI displaying errors from MemoryEntry.error field
7. CLI --show-history flag works with empty history and populated history
8. Interactive menu showing history with error entries

---

## ASSUMPTIONS

1. **Exception Handling:** Service catches exceptions and returns error-state MemoryEntry. Does NOT re-raise.
2. **UUID Strategy:** UUID v4 (random), stored as string in JSON.
3. **Error Scope:** Any Exception is caught and recorded (ValueError, TypeError, etc.).
4. **Interactive Error Recovery:** After error, menu returns to prompt (does not crash).
5. **--show-history Precedence:** If both --show-history and --operation provided, --show-history executes first and exits.
6. **CalculationResult Coexistence:** Keep CalculationResult class for backward compat, but only use MemoryEntry in new code.

---

## IMPLEMENTATION ORDER

1. Create MemoryEntry class
2. Update models/__init__.py
3. Update CalculatorService (core logic change)
4. Update JsonStorage (serialization)
5. Update CalculatorCLI (display)
6. Update __main__.py (CLI wiring)
7. Create new test files
8. Update existing test files

Each step builds on the previous one and can be tested independently.
