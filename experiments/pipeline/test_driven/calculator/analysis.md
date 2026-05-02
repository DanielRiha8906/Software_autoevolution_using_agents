# Calculator Application Analysis: Execution Time Tracking

**Date:** 2026-05-01  
**Task:** Analyze current CalculationResult structure and CalculatorService implementation to determine what changes are needed to add execution time tracking in milliseconds.

---

## 1. Current CalculationResult Structure

**File:** `src/models/calculation_result.py`

### Current Fields
```python
@dataclass
class CalculationResult:
    operation: str              # e.g., "add", "subtract"
    operand_a: float            # First operand
    operand_b: float            # Second operand
    result: float               # Calculation result
    timestamp: str = field(default="")  # ISO format datetime
```

### Current Behavior
- **Auto-timestamping:** If `timestamp` is empty, `__post_init__()` sets it to `datetime.now().isoformat()`
- **Serialization:** `to_dict()` uses `asdict()`, works bidirectionally with `from_dict()`
- **Display:** `__str__()` formats operands and result for readability, handling both int and float display

### Key Observation
The class currently has **no execution time tracking**. All fields map directly to calculation metadata and results, not performance metrics.

---

## 2. Current CalculatorService Implementation

**File:** `src/services/calculator_service.py`

### Current Flow
```python
def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
    # 1. Perform calculation (delegated to Calculator)
    result = self.calculator.calculate(operation, a, b)
    
    # 2. Create CalculationResult with no timing information
    calc_result = CalculationResult(
        operation=operation.value,
        operand_a=a,
        operand_b=b,
        result=result,
        # timestamp auto-populated by __post_init__
    )
    
    # 3. Persist to storage
    self.storage.save(calc_result)
    
    return calc_result
```

### Key Observations
- **No timing:** The entire perform() method takes no measurements
- **Timing Point:** Would need to measure time between start and completion of `calculator.calculate()`
- **Where to Measure:** Between line 13 (before calculation) and assignment (after calculation)

---

## 3. Required Changes for Execution Time Tracking

### 3.1 Add `execution_time_ms` Field to CalculationResult

**File:** `src/models/calculation_result.py`

Current dataclass has 5 fields. Need to add:
```python
execution_time_ms: float = field(default=0.0)  # or use field(default_factory=...)
```

**Design Decision:** 
- Type: `float` (allows fractional milliseconds for precision)
- Default: `0.0` (no timing information)
- Optional in `__post_init__`: Auto-timing not needed for this field like timestamp
- Serialization: Automatically included via `asdict()` in `to_dict()`

### 3.2 Modify CalculatorService.perform()

**File:** `src/services/calculator_service.py`

Need to add timing instrumentation:

```python
import time  # Add import

def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
    # Measure time for calculation phase
    start_time = time.perf_counter()
    result = self.calculator.calculate(operation, a, b)
    end_time = time.perf_counter()
    
    # Convert to milliseconds
    execution_time_ms = (end_time - start_time) * 1000
    
    # Create result with execution time
    calc_result = CalculationResult(
        operation=operation.value,
        operand_a=a,
        operand_b=b,
        result=result,
        execution_time_ms=execution_time_ms,  # NEW FIELD
    )
    
    self.storage.save(calc_result)
    return calc_result
```

**Timing Considerations:**
- **Scope:** Measures only `calculator.calculate()`, not storage overhead
- **Precision:** `time.perf_counter()` is high-resolution, immune to system clock adjustments
- **Conversion:** `(seconds) * 1000 = milliseconds`
- **Error Handling:** Division by zero in Calculator.divide() raises ValueError before timing completes (timing not saved for failed operations)

---

## 4. Files That Will Need Modification

### Primary Changes
1. **`src/models/calculation_result.py`**
   - Add `execution_time_ms: float` field
   - No changes to `__post_init__()`, `to_dict()`, `from_dict()`, or `__str__()` logic
   - Default value ensures backward compatibility with deserialization

2. **`src/services/calculator_service.py`**
   - Add `import time`
   - Wrap calculation in timing code
   - Pass `execution_time_ms` to CalculationResult constructor

### Files With No Changes Required
- `src/models/operation.py` — operation enum, unaffected
- `src/services/calculator.py` — core logic unchanged
- `src/storage/json_storage.py` — serialization handled automatically by `to_dict()`
- `src/cli/calculator_cli.py` — display logic unchanged (can optionally show execution_time_ms)
- `tests/*` — existing tests should continue passing (new field has default value)

---

## 5. Key Design Decisions

### Q1: How to Measure Time?
**Decision:** Use `time.perf_counter()`
- **Why:** High-resolution timer, immune to system clock adjustments
- **Alternative:** `time.time()` is less precise; `time.process_time()` excludes I/O

### Q2: What to Measure?
**Decision:** Time inside `perform()`, from start of `calculator.calculate()` to return
- **What's included:** Arithmetic operations only
- **What's excluded:** Storage save time, object instantiation, method dispatch overhead
- **Rationale:** Isolates pure calculation performance

### Q3: Scope of Change to CalculationResult?
**Decision:** Add field, keep existing fields and methods unchanged
- **Why:** Backward compatible with deserialization, no cascade changes to `__str__()` or display
- **Storage:** Field automatically serialized to JSON via `asdict()`
- **Deserialization:** `from_dict()` works because field has default value

### Q4: When Is execution_time_ms Set?
**Decision:** Only when calculation succeeds
- **Failure case:** ValueError from division by zero → exception thrown → CalculationResult never created → nothing saved
- **Implication:** Failed operations don't have execution_time_ms recorded

### Q5: Precision and Unit
**Decision:** `float` type, measured in milliseconds
- **Why:** Floating-point allows fractional milliseconds (e.g., 0.123 ms)
- **Alternative:** Could use int microseconds, but ms is user-facing and more readable

---

## 6. Backward Compatibility

### Existing Data
- Old saved calculations in `artifacts/calculations.json` lack `execution_time_ms`
- When loaded via `from_dict()`, field defaults to `0.0`
- Display will show default value without error

### Existing Tests
- All 38 existing tests should pass unchanged
- Tests don't assert on execution_time_ms (it will exist but not be checked)
- Mocked CalculationResult objects must have execution_time_ms if calling asdict() or to_dict()

---

## Summary

**What to change:**
1. Add `execution_time_ms: float = field(default=0.0)` to CalculationResult dataclass
2. Import `time` module in CalculatorService
3. Wrap `calculator.calculate()` with `time.perf_counter()` calls in `perform()` method
4. Pass calculated execution time to CalculationResult constructor

**What NOT to change:**
- Any calculation logic (Calculator class)
- Any storage logic (JsonStorage class)
- Any display logic (CalculatorCLI class) — optional to show execution_time_ms later

**Files affected:** 2 files (`src/models/calculation_result.py`, `src/services/calculator_service.py`)
