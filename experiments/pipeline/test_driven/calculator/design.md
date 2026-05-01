# Execution Time Tracking - Implementation Design

## Overview

Add execution time tracking to the calculator application to measure and record the elapsed time in milliseconds for each calculation operation.

## Changes Required

### 1. CalculationResult Model (`src/models/calculation_result.py`)

**Add field:**
- `execution_time_ms: float = field(default=0.0)` — stores calculation execution time in milliseconds

**Harden `from_dict()` method:**
- Modify to use `data.get('execution_time_ms', 0.0)` pattern for backward compatibility with existing JSON files that don't have this field
- Current implementation `cls(**data)` will fail if execution_time_ms is missing from loaded data

**Why:** 
- Existing JSON records won't have execution_time_ms field
- Default value 0.0 ensures old records load without error
- New records will have actual measured values

### 2. CalculatorService (`src/services/calculator_service.py`)

**Add import:**
- `import time` at the top of the file

**Modify `perform()` method:**
```
1. Record start_time using time.perf_counter() before calling calculator.calculate()
2. Call calculator.calculate(operation, a, b) 
3. Record end_time immediately after
4. Calculate elapsed_ms = (end_time - start_time) * 1000
5. Pass execution_time_ms parameter when creating CalculationResult
```

**Scope:** Measure only the calculator.calculate() call, not CalculationResult creation or storage.save()

**Error handling:** If calculator.calculate() raises exception, timing is not recorded (exception propagates, no result created)

### 3. No Changes Needed

- `Calculator` — timing is measured at service layer, not calculator layer
- `JsonStorage` — automatically includes execution_time_ms via CalculationResult.to_dict()

## Backward Compatibility

1. **Constructor:** `CalculationResult(operation, operand_a, operand_b, result)` works without execution_time_ms (defaults to 0.0)
2. **Serialization:** Old JSON without execution_time_ms loads successfully with default value 0.0
3. **New code:** Can optionally pass execution_time_ms parameter

## Test Coverage Expectations

The implementation should satisfy:
- execution_time_ms field exists and is a numeric type
- execution_time_ms is non-negative
- CalculatorService.perform() sets execution_time_ms to measured time
- Serialization to_dict() includes execution_time_ms
- Deserialization from_dict() restores execution_time_ms
- Existing fields remain unchanged and functional
