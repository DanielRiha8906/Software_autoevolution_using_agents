# Execution Time Tracking for CalculationResult — Analysis Report

## Task Summary

Implement execution time tracking for the `CalculationResult` class to measure and store the duration (in milliseconds) of arithmetic calculations. The feature must:
- Add an `execution_time_ms` field to `CalculationResult`
- Populate this field during the calculation flow in `CalculatorService.perform()`
- Include it in serialization/deserialization (`to_dict()` / `from_dict()`)
- Support both implicit initialization (when timing is measured automatically) and explicit initialization (for deserialization tests)
- Preserve all existing constructor and method signatures

---

## Current Structure Analysis

### 1. CalculationResult (src/models/calculation_result.py)

**Current structure:**
```python
@dataclass
class CalculationResult:
    operation: str
    operand_a: float
    operand_b: float
    result: float
    timestamp: str = field(default="")
```

**Current behavior:**
- Uses `@dataclass` with `asdict()` for serialization
- Has a `__post_init__()` method that auto-generates `timestamp` if not provided
- `to_dict()` returns `asdict(self)` — includes all fields
- `from_dict(cls, data)` constructs via `cls(**data)` — accepts all keys as kwargs
- `__str__()` formats for display using the `_SYMBOLS` map

**Current test coverage:**
- Existing tests in `test_calculator_service.py` verify timestamp is generated
- No tests for the execution_time field yet

### 2. CalculatorService (src/services/calculator_service.py)

**Current flow in `perform()` method (lines 12–21):**
```
1. Call calculator.calculate(operation, a, b) → returns numeric result
2. Create CalculationResult with operation, operand_a, operand_b, result
3. Call storage.save(calc_result)
4. Return calc_result
```

**Timing insertion point:**
- Timing measurement must wrap the `calculator.calculate()` call
- Measurement should happen before `CalculationResult` instantiation
- The computed duration should be passed to the `CalculationResult` constructor

**Current state:**
- No timing instrumentation
- No reference to time module

### 3. JsonStorage (src/storage/json_storage.py)

**Current serialization:**
- `save()` calls `result.to_dict()` and stores the dict
- `load_all()` calls `CalculationResult.from_dict()` on each stored dict
- Uses standard `json` module (from Python stdlib, no 3rd party deps)

**Impact on execution_time_ms:**
- If `execution_time_ms` is a dataclass field, it will be included in `asdict()` output automatically
- If it's provided in the dict during `from_dict()`, it will be passed as a kwarg to the constructor
- No changes needed to JsonStorage — it will transparently handle the new field

### 4. Calculator (src/services/calculator.py)

**Status:** No changes required
- Pure arithmetic logic; timing wrapper will be in CalculatorService, not here

---

## Test Requirements Analysis

The test suite (provided in task description) expects:

1. **test_calculation_result_has_execution_time_ms()**
   - Verify `execution_time_ms` attribute exists after construction
   - Constructed with positional args: `operation, operand_a, operand_b, result`

2. **test_execution_time_ms_is_numeric()**
   - Type check: `isinstance(execution_time_ms, (int, float))`

3. **test_execution_time_ms_is_non_negative()**
   - Verify `>= 0` (never negative)

4. **test_service_sets_execution_time_ms(tmp_path)**
   - Call `CalculatorService.perform()` and verify the returned result has `execution_time_ms >= 0`
   - This confirms automatic population during the service flow

5. **test_execution_time_ms_included_in_serialization()**
   - `result.to_dict()` must include `execution_time_ms` key

6. **test_execution_time_ms_restored_from_serialization()**
   - Construct with `execution_time_ms=12.5` explicitly
   - Call `to_dict()` then `from_dict()` and verify value is preserved
   - Use `pytest.approx()` for floating-point comparison

7. **test_existing_fields_unchanged()**
   - Verify backward compatibility: `operation, operand_a, operand_b, result` still work

**Key implications:**
- Constructor must accept `execution_time_ms` as optional parameter (tests 1, 6)
- Must support default initialization without timing provided (tests 1–3)
- Default value should be non-negative (probably `0` or auto-measured)
- Serialization/deserialization must round-trip the value

---

## Files That Need Modification

### 1. src/models/calculation_result.py — **REQUIRED**

**Changes needed:**
- Add `execution_time_ms: float = field(default=0.0)` to the dataclass
- Keep the field optional with a default value (for backward compatibility)
- No changes to `to_dict()` (asdict will include it automatically)
- No changes to `from_dict()` (cls(**data) will accept it if present)
- No changes to `__post_init__()` (timestamp logic unchanged)
- No changes to `__str__()` (timing display not required by tests)

**Rationale:**
- Using `field(default=0.0)` ensures tests 1–3 pass (object creation with default)
- When `execution_time_ms` is not provided during deserialization, it defaults to `0.0`
- When provided (test 6), the value is accepted and stored
- Dataclass + `asdict()` automatically include the field in serialization

### 2. src/services/calculator_service.py — **REQUIRED**

**Changes needed:**
- Import `time` module (Python stdlib, standard for time measurement)
- Wrap the `calculator.calculate()` call with timing:
  - Record start time before the call
  - Record end time after the call
  - Calculate `duration_ms = (end - start) * 1000` (convert seconds to milliseconds)
- Pass the computed `execution_time_ms` to the `CalculationResult` constructor

**Code pattern:**
```python
import time

# In perform() method:
start = time.time()
result = self.calculator.calculate(operation, a, b)
end = time.time()
execution_time_ms = (end - start) * 1000

calc_result = CalculationResult(
    operation=operation.value,
    operand_a=a,
    operand_b=b,
    result=result,
    execution_time_ms=execution_time_ms,
)
```

**Rationale:**
- `time.time()` is the standard Python method for measuring wall-clock duration
- Multiplication by 1000 converts from seconds to milliseconds (test requirement)
- Measurement wraps only the arithmetic logic, not storage I/O
- Constructor now receives the measured value instead of relying on a default

### 3. src/models/operation.py — **NOT REQUIRED**
No changes needed.

### 4. src/services/calculator.py — **NOT REQUIRED**
No changes needed.

### 5. src/storage/json_storage.py — **NOT REQUIRED**
No changes needed; will automatically serialize/deserialize the new field.

### 6. tests/ — **NOT REQUIRED**
Task explicitly states: "Do not modify the tests."

---

## Execution Time Measurement Strategy

### Where to Measure
- **Start point:** Immediately before `self.calculator.calculate(operation, a, b)`
- **End point:** Immediately after the call returns
- **Why here:** Measures only the arithmetic operation, not I/O or object construction

### Unit: Milliseconds
- Python's `time.time()` returns seconds as a float
- Formula: `duration_ms = (end_time - start_time) * 1000`
- Float precision is acceptable per tests (test 2: `isinstance(..., (int, float))`)

### Non-negative Guarantee
- `time.time()` is monotonic within a single function scope
- Duration will always be >= 0 (end >= start)
- Test 3 will pass automatically

### Default Value
- Set to `0.0` in dataclass to satisfy tests 1–3 (object creation without timing)
- The service layer will override with actual measurement during normal use
- Deserialization will accept a value from storage if present (test 6)

---

## Backward Compatibility Considerations

1. **Constructor compatibility:** The new field is optional with a default, so existing code that creates `CalculationResult(op, a, b, result)` still works.

2. **Serialization:** Existing JSON records without `execution_time_ms` will deserialize to `0.0`, which is safe and semantically neutral.

3. **Existing tests:** No changes needed to existing test files. The new tests are additive.

4. **Public interfaces:** No method signatures change; no new public methods added.

---

## Summary of Changes

| File | Change Type | Details |
|------|-------------|---------|
| `src/models/calculation_result.py` | Add field | Add `execution_time_ms: float = field(default=0.0)` to dataclass |
| `src/services/calculator_service.py` | Timing instrumentation | Import `time`, wrap `calculator.calculate()` call, pass duration to `CalculationResult` |
| `src/storage/json_storage.py` | None | Serialization handled automatically |
| `src/services/calculator.py` | None | No changes |
| `src/models/operation.py` | None | No changes |
| `tests/` | None | Task restriction: do not modify |

---

## Test Validation Mapping

| Test | Validation | Expected Result |
|------|-----------|-----------------|
| `test_calculation_result_has_execution_time_ms()` | Attribute existence | Pass — field will be in dataclass |
| `test_execution_time_ms_is_numeric()` | Type check | Pass — float type from `field(default=0.0)` |
| `test_execution_time_ms_is_non_negative()` | Value check | Pass — time delta is always >= 0 |
| `test_service_sets_execution_time_ms()` | Integration | Pass — CalculatorService measures and passes duration |
| `test_execution_time_ms_included_in_serialization()` | Serialization | Pass — `asdict()` includes all fields |
| `test_execution_time_ms_restored_from_serialization()` | Round-trip | Pass — `from_dict()` accepts the value |
| `test_existing_fields_unchanged()` | Backward compat | Pass — no signature changes to constructor |

---

## No Ambiguities Detected

All test requirements are clear and directly implementable from the provided test suite. The timing measurement point is unambiguous (before/after `calculator.calculate()`). The unit (milliseconds) is explicit. The default behavior (0.0 when not measured) is safe and well-defined.
