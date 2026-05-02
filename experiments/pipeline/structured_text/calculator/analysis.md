# Task 01: Add execution time tracking to calculation results

## Analysis

### Current CalculationResult Structure

The CalculationResult dataclass is defined at:
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/models/calculation_result.py`

Current fields:
- `operation: str` (e.g., "add", "subtract")
- `operand_a: float` (first operand)
- `operand_b: float` (second operand)
- `result: float` (calculated result)
- `timestamp: str` (ISO format, auto-populated in __post_init__)

The dataclass provides:
- `to_dict()` — converts to dictionary (uses asdict)
- `from_dict()` — reconstructs from dictionary
- `__str__()` — human-readable format for display

### Where Calculations Are Executed

**Primary execution path:** CalculatorService.perform()
- **File:** `src/services/calculator_service.py`, lines 12-21
- **Flow:**
  1. Calls `Calculator.calculate(operation, a, b)` to get the numeric result
  2. Creates a CalculationResult instance with operation, operands, and result
  3. Saves the result to storage
  4. Returns the CalculationResult

**The actual arithmetic happens in:** Calculator class
- **File:** `src/services/calculator.py`
- Methods: `add()`, `subtract()`, `multiply()`, `divide()` (lines 5-17)
- All delegate to `calculate()` method which dispatches to the appropriate operation

**No timing measurement currently exists** — the entire execution path from Calculator.calculate() through CalculationResult creation happens without timing.

### Calculation Invocation Points

Three paths invoke calculations:

1. **Interactive mode:** CalculatorCLI.run_interactive() → service.perform()
   - File: `src/cli/calculator_cli.py`, line 52

2. **Command mode:** CalculatorCLI.run_command() → service.perform()
   - File: `src/cli/calculator_cli.py`, line 60

3. **History retrieval:** CalculatorService.get_history() → JsonStorage.load_all()
   - File: `src/services/calculator_service.py`, line 23-24
   - This loads pre-calculated results, no timing needed here

All active calculations funnel through `CalculatorService.perform()`.

### How Timing Should Be Injected

**Recommended approach:** Measure execution time in `CalculatorService.perform()` method

**Rationale:**
- Single point of injection covers both CLI entry paths
- Measures entire operation including Calculator dispatch (where most real work happens)
- Keeps timing logic at the service layer, not in models
- Clean separation: timing is implementation detail of service, not part of data model

**Measurement technique:**
- Use `time.perf_counter()` (preferred over time.time() for benchmarks)
- Measure from just before `Calculator.calculate()` call until after result creation
- Convert to milliseconds (multiply by 1000 and round)

**Implementation location:**
```
File: src/services/calculator_service.py, method perform()
1. Record start time before: result = self.calculator.calculate(...)
2. Record end time after result creation
3. Calculate execution_time_ms = (end - start) * 1000
4. Pass to CalculationResult constructor
```

### Dependencies & Potential Issues

**1. Backward Compatibility with Serialization**

Current state:
- `CalculationResult.to_dict()` uses `asdict()` — automatically includes all fields
- `CalculationResult.from_dict()` uses `**data` unpacking — accepts extra keys gracefully
- Storage (JsonStorage) relies on to_dict/from_dict round-trip

**Problem if not handled:**
- If `execution_time_ms` is not in old JSON records, `from_dict()` will fail when unpacking because the field has no default
- Old calculation records in `artifacts/calculations.json` don't have this field

**Solution:**
- Give `execution_time_ms` a default value (e.g., 0.0 or None)
- Make it optional: `execution_time_ms: float = field(default=0.0)`
- This allows loading old records without the field and assigning a sensible default

**2. Timing Measurement Accuracy**

- Python's `time.perf_counter()` is monotonic and high-resolution
- Calculations are typically fast (microseconds to milliseconds range)
- Rounding to milliseconds is reasonable and matches requirement
- No external dependencies needed (time module is builtin)

**3. Field Naming Convention**

Current naming pattern in CalculationResult:
- `operand_a` (snake_case)
- `operand_b` (snake_case)
- `timestamp` (snake_case)

**Proposed field:** `execution_time_ms`
- Follows snake_case convention
- Includes unit suffix (_ms) for clarity
- Matches common timing convention in Python (Django, etc.)

### Required Changes

**1. CalculationResult dataclass (src/models/calculation_result.py)**
- Add field: `execution_time_ms: float = field(default=0.0)`
- Update `__str__()` if timing should be displayed (decision deferred to architect)

**2. CalculatorService.perform() (src/services/calculator_service.py)**
- Import `time` module
- Wrap `Calculator.calculate()` call with timing
- Pass measured time to CalculationResult constructor

**3. Tests**
- Update mock CalculationResult instantiation to handle new field
- Add test verifying execution_time_ms is set and > 0
- Verify old records without field can still load

**4. JSON Storage (no code changes needed)**
- to_dict/from_dict already handle new field automatically
- Default value ensures old records load without error

### Scope Summary

**In scope (Must requirements):**
- Add `execution_time_ms` to CalculationResult dataclass
- Populate it for every calculation in CalculatorService.perform()
- Ensure measurable and in milliseconds

**In scope (Should requirements):**
- Accurate measurement (perf_counter is appropriate)
- Naming convention (execution_time_ms follows existing pattern)
- Backward compatibility (default field value in dataclass)

**Out of scope:**
- CLI display of execution time (architect decides if shown in output)
- Aggregated timing statistics or reports
- Timing of individual arithmetic operations (only service-level timing)
- Changes to public API beyond new attribute

### Backward Compatibility Details

**Current state of calculations.json:**
- Contains 4 records, each with: operation, operand_a, operand_b, result, timestamp
- No execution_time_ms field

**After change:**
- Old records can load because execution_time_ms has default=0.0
- New records will include execution_time_ms
- Mixed old/new records in same file will work (old ones have 0.0, new ones have measured time)
- No migration script needed

**API compatibility:**
- Existing code calling `service.perform()` continues to work (returns same CalculationResult type)
- CalculationResult constructor requires execution_time_ms parameter unless given default
- Default value makes it optional during instantiation

### Summary of Key Findings

1. **Single injection point:** CalculatorService.perform() is the only place calculations are invoked
2. **No timing infrastructure exists:** Currently measuring nothing; clean slate for implementation
3. **Storage layer handles new fields automatically:** to_dict/from_dict patterns are generic
4. **Backward compatibility is critical:** Old JSON records must still load
5. **Naming is straightforward:** execution_time_ms follows conventions and is self-documenting
6. **Measurement is simple:** time.perf_counter() + millisecond conversion, no external dependencies
