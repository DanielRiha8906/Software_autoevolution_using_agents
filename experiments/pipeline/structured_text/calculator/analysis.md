# Execution Time Tracking Analysis — Calculator Project

## Current Structure Overview

**Architecture**: Layered OOP design with clear separation of concerns:
- **Models** (`src/models/`): `Operation` enum and `CalculationResult` dataclass
- **Services** (`src/services/`): `Calculator` (pure arithmetic) and `CalculatorService` (orchestration + persistence)
- **Storage** (`src/storage/`): `JsonStorage` for persistence to `artifacts/calculations.json`
- **CLI** (`src/cli/`): `CalculatorCLI` for interactive and one-shot command modes

**Test coverage**: 38 tests across four modules (calculator, service, storage, CLI)

---

## CalculationResult Class

**Location**: `/src/models/calculation_result.py`

**Current definition** (lines 8-32):
```python
@dataclass
class CalculationResult:
    operation: str
    operand_a: float
    operand_b: float
    result: float
    timestamp: str = field(default="")
```

**Key characteristics**:
- Dataclass with 5 attributes
- `timestamp` initialized in `__post_init__()` to current ISO-format time if not provided
- Provides `to_dict()` and `from_dict()` for serialization/deserialization
- Custom `__str__()` for display (converts to symbol notation and formats numbers)
- Created in `CalculatorService.perform()` (line 14-19) after calculation completes

**Serialization**: Uses `asdict()` from dataclasses, so new attributes automatically serialize to JSON

---

## Timing Measurement Locations

**Where calculations happen**:

1. **Pure arithmetic** (`src/services/calculator.py`):
   - Individual methods: `add()`, `subtract()`, `multiply()`, `divide()` (lines 5-17)
   - Dispatcher: `calculate()` routes by `Operation` enum (lines 19-28)
   - These are lightweight operations; direct timing would include only the arithmetic

2. **Orchestration** (`src/services/calculator_service.py`, `perform()` method, lines 12-21):
   - Current flow:
     ```
     1. Call calculator.calculate(operation, a, b)  ← produces float result
     2. Construct CalculationResult dataclass
     3. Call storage.save(calc_result)
     4. Return calc_result
     ```
   - Timing options:
     - **Narrow**: Only `calculator.calculate()` call (arithmetic only)
     - **Broad**: Entire `perform()` call (includes dataclass construction + storage persistence)

3. **Storage** (`src/storage/json_storage.py`, `save()` method, lines 11-14):
   - Reads existing records from file
   - Appends new record
   - Writes back to disk
   - This is the most time-variable operation due to I/O

---

## Implementation Considerations

### Backward Compatibility
- **CalculationResult serialization**: Adding a new dataclass field automatically includes it in `to_dict()` and `asdict()` output
- **from_dict() deserialization**: Currently uses `cls(**data)`, which will fail if JSON contains `execution_time_ms` but old code instantiates without it
  - Mitigation: Set `execution_time_ms` with a sensible default (e.g., `field(default=0)` or `field(default_factory=float)`)
  - This allows loading old JSON (without the field) and creating new records with timing data simultaneously

- **CLI display**: Currently calls `entry.timestamp` in `_show_history()` (line 101); adding timing will not break this as it displays all attributes via `__str__()`

### Naming Conventions
- Consistent with existing codebase: snake_case for attributes (`operand_a`, `operand_b`, `execution_time_ms`)
- Unit clarity: `_ms` suffix (milliseconds) is explicit and aligns with common conventions

### Measurement Accuracy
- **Built-in**: Use `time.perf_counter()` (available in standard library since Python 3.3)
  - Monotonic clock, nanosecond-resolution, ideal for elapsed time
  - No external dependencies required
- **Precision**: Can compute milliseconds with microsecond precision: `(end - start) * 1000` yielding a float
- **Scope decision**: Measure only `calculator.calculate()` call (narrow scope) for consistency; storage I/O is not part of "calculation"

### Reusable Timing Mechanism
- **Option 1**: Add static/class method to `Calculator` or create a utility module
- **Option 2**: Use Python's `time.perf_counter()` directly in `CalculatorService.perform()`
- **Option 3**: Decorator pattern for timing (more complex, not needed for current scope)
- **Rationale**: Given "Won't: External libraries" constraint, prefer simple, direct timing in `perform()` method rather than over-engineering

---

## Identified Constraints & Risks

### 1. Test compatibility (Medium impact)
- **Current tests**: 38 tests create `CalculationResult` instances with positional args or explicit kwargs
- **Mock tests** (`test_calculator_service.py`): Use tuple unpacking from `storage.save.call_args` (line 33)
- **Test data** (`test_json_storage.py`): Hard-coded timestamp string `_TS = "2026-01-01T00:00:00"`
- **Risk**: Adding `execution_time_ms` field changes constructor signature; existing test instantiation may fail if not carefully ordered
- **Mitigation**: Place new field after `timestamp` (or with a default) to preserve positional arg compatibility, or convert to keyword-only args

### 2. JSON persistence (Low impact)
- Storage uses `json.dump()` which handles floats natively
- Timing data persists automatically via `to_dict()` → `json.dump()`
- **No schema migration** needed; old JSON without `execution_time_ms` can still load (if default provided)

### 3. CLI output (Low impact)
- Current `__str__()` displays: `"a symbol b = r"` (operands and result)
- Timing data not displayed in summary view; history view would need optional enhancement
- Backward compatible as-is

### 4. Measurement timing (Medium impact)
- **When to start/stop timer?**
  - Start: Immediately before `calculator.calculate()` call
  - End: Immediately after result returned
  - Must occur in `CalculatorService.perform()` since that's where orchestration happens
- **Edge case**: Division by zero raises exception before result is computed; timing will not be recorded (intentional—failed calculations should not be tracked)

---

## Suggested Implementation Approach

1. **Add field to CalculationResult**:
   - New field: `execution_time_ms: float = field(default=0.0)`
   - Position: After `timestamp` field
   - Rationale: Maintains optional/default-initialized pattern; backward-compatible JSON loading

2. **Measure in CalculatorService.perform()**:
   - Import `time.perf_counter` at top of file
   - Wrap `calculator.calculate()` call with timing:
     ```python
     start = time.perf_counter()
     result = self.calculator.calculate(operation, a, b)
     elapsed = (time.perf_counter() - start) * 1000
     ```
   - Pass elapsed time to `CalculationResult` constructor

3. **Update tests**:
   - Verify `execution_time_ms` field exists and is a float ≥ 0
   - Mock storage calls will need to validate new field presence
   - Backward-compat test: Load old JSON (without timing field) and verify default=0.0 applied

4. **No changes needed to**:
   - CLI display (works via `__str__()` and dictionary serialization)
   - Storage layer (automatic via `to_dict()` and `json.dump()`)
   - Calculator class (measurement is at service level, not arithmetic level)

---

## Risk Summary

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Test instantiation breakage | Medium | Use default value; update test constructors systematically |
| Timing accuracy under load | Low | `perf_counter()` is monotonic and precise |
| JSON backward compatibility | Low | Default value handles missing field from old records |
| Division-by-zero skips timing | Low | Intentional; only successful calculations are tracked |

---

## Ambiguities & Assumptions

1. **Scope of measurement**: Assuming "execution time of calculation" refers to arithmetic only (not persistence or UI). If full round-trip timing is desired, measurement point moves to start/end of `perform()` method.

2. **Default value for new records**: Assuming `0.0` milliseconds is acceptable default for old records loaded from JSON. Alternative: `None` with nullable type, then migrate display logic.

3. **Precision requirement**: Assuming millisecond precision (float with 3 decimal places) is sufficient. If nanosecond precision needed, store as `int` nanoseconds instead.

4. **CLI display of timing**: No requirement stated. Assuming timing data is stored but not displayed in current CLI (can be added in future enhancement if needed).

