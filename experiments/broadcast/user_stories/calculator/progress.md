# Task Progress

## Task 01

**Description:** Add execution time tracking to calculation results

**Status:** ✅ Complete

### Broadcast Evaluation

**Candidate A:**
- Approach: Measured execution time in CalculatorService.perform() around Calculator.calculate() call
- Test Result: 38/38 passed
- Implementation: Added execution_time_ms field with default=0.0 for backward compatibility

**Candidate B:**
- Approach: Measured execution time in CalculatorService.perform() around Calculator.calculate() call
- Test Result: 38/38 passed
- Implementation: Added execution_time_ms field with default=0.0 for backward compatibility

**Candidate C:**
- Approach: Measured execution time in CalculatorService.perform() around Calculator.calculate() call
- Test Result: 38/38 passed
- Implementation: Added execution_time_ms field with default=0.0 for backward compatibility

**Winner:** Candidate A (identical implementations, all passed all tests)

### Files Changed

1. `src/models/calculation_result.py`
   - Added `execution_time_ms: float = field(default=0.0)` field to CalculationResult dataclass

2. `src/services/calculator_service.py`
   - Added `import time`
   - Wrapped `calculator.calculate()` call with `time.perf_counter()` timing
   - Pass calculated `execution_time_ms` to CalculationResult constructor

### Test Results

- Total tests: 38
- Passed: 38
- Failed: 0
- Status: ✅ All tests pass

### Requirements Met

**Acceptance Criteria:**
- ✅ CalculationResult has an execution_time_ms attribute representing elapsed time in milliseconds
- ✅ The attribute is populated automatically for every calculation — no manual input required
- ✅ Measurement uses only the standard library (time.perf_counter())
- ✅ Existing code that constructs or reads CalculationResult continues to work without changes (backward compatibility with default=0.0)

Duration: 339.8s | Cost: $0.684623 USD | Turns: 48

## Task 02

**Description:** Add square, square root, power, and modulo operations

**Status:** ✅ Complete

### Broadcast Evaluation

**Candidate A:**
- Approach: Added SQUARE, SQRT, POWER, MODULO enum members. Implemented square(), sqrt(), power(), modulo() methods in Calculator. Added error handling for negative sqrt and modulo by zero. Updated CLI menu and __main__.py argparse.
- Test Result: 31/38 passed (7 CLI tests failed due to menu index changes)
- Key feature: Operations accessible via interactive menu and one-shot CLI flags

**Candidate B:**
- Approach: Added SQUARE, SQRT, POWER, MODULO enum members. Implemented square(), sqrt(), power(), modulo() methods in Calculator with math.sqrt() for sqrt operation. Added operation symbols to calculation_result.py. Updated CLI menu and __main__.py argparse.
- Test Result: 31/38 passed (7 CLI tests failed due to menu index changes)
- Key feature: Display symbols (², √, ^, %) for new operations

**Candidate C:**
- Approach: Added SQUARE, SQRT, POWER, MODULO enum members. Implemented square(), sqrt(), power(), modulo() methods in Calculator. Updated test_cli.py to fix menu index references and operation validity checks. Updated CLI menu and __main__.py argparse.
- Test Result: 38/38 passed ✅
- Key feature: Fixed tests to accommodate new menu structure

**Winner:** Candidate C (38/38 tests passed)

### Files Changed

1. `src/models/operation.py`
   - Added enum members: SQUARE, SQRT, POWER, MODULO
   - Updated from_string() method to recognize new operations

2. `src/models/calculation_result.py`
   - Added _SYMBOLS dict entries for new operations: "square": "²", "sqrt": "√", "power": "^", "modulo": "%"

3. `src/services/calculator.py`
   - Added import math
   - Implemented square(a, b): returns a²
   - Implemented sqrt(a, b): returns √a with ValueError for negative a
   - Implemented power(a, b): returns a^b (supports negative and fractional exponents)
   - Implemented modulo(a, b): returns a % b with ValueError for b == 0
   - Updated calculate() dispatch dict to include new operations

4. `src/cli/calculator_cli.py`
   - Added four new operations to _MENU list:
     - (Operation.SQUARE, "Square")
     - (Operation.SQRT, "Square Root")
     - (Operation.POWER, "Power")
     - (Operation.MODULO, "Modulo")

5. `src/__main__.py`
   - Updated argparse --operation choices to include "square", "sqrt", "power", "modulo"
   - Updated usage string and help text to show all 8 operations

6. `tests/test_cli.py`
   - Updated test_invalid_operation_exits to test "invalid_op" instead of "modulo" (modulo is now valid)
   - Updated test_exit_choice, test_add_operation, test_invalid_choice_retries, test_invalid_number_retries, test_history_empty, test_history_shows_entries to reflect menu index changes (exit moved from 6 to 10, history from 5 to 9)

### Test Results

- Total tests: 38
- Passed: 38
- Failed: 0
- Status: ✅ All tests pass

### Acceptance Criteria Met

- ✅ All four operations available: square(x), sqrt(x), power(x, y), modulo(x, y)
- ✅ Each operation follows existing interface (two float parameters)
- ✅ sqrt of negative number raises ValueError
- ✅ modulo by zero raises ValueError
- ✅ power with negative exponents works (e.g., 2^-1 = 0.5)
- ✅ power with fractional exponents works (e.g., 4^0.5 = 2.0)
- ✅ No existing operations duplicated or renamed
- ✅ All operations accessible via python -m src:
  - Interactive menu with all 8 operations
  - One-shot CLI: python -m src --operation {square|sqrt|power|modulo} A B
  - Help shows all operations: python -m src --help

Duration: 399.0s | Cost: $0.859193 USD | Turns: 48

## Task 03

**Description:** Create a `MemoryEntry` class for the calculator's history feature that captures everything about a single calculation attempt

**Status:** ✅ Complete

### Broadcast Evaluation

**Candidate A:**
- Approach: Dataclass-based MemoryEntry with UUID-based unique identifiers, factory methods (create_success/create_failure), and separate calculations_memory.json storage file
- Test Result: 67/67 tests passed
- Key features: Backward compatible with existing calculations.json, separate memory storage, validation in __post_init__

**Candidate B:**
- Approach: Timestamp-based ID generation (nanosecond precision), minimal initialization, is_success property, compact JSON representation
- Test Result: 62/62 tests passed
- Key features: Simpler ID scheme, inline validation, flexible error handling

**Candidate C:**
- Approach: Abstract base class with ResultEntry and ErrorEntry subclasses, counter-based sequential IDs, polymorphic serialization, type-safe design with docstrings
- Test Result: 98/98 tests passed ✅
- Key features: Strong typing, subclass pattern, comprehensive test coverage, separate CLI commands for memory vs calculation history

**Winner:** Candidate C (98/98 tests passed - highest coverage with type-safe subclass design)

### Files Changed

1. **src/models/memory_entry.py** (NEW)
   - Abstract MemoryEntry base class with common fields: entry_id, operation, operand_a, operand_b, timestamp, execution_time_ms
   - ResultEntry subclass for successful calculations with result field
   - ErrorEntry subclass for failed calculations with error_message field
   - Counter-based sequential ID generation (_id_counter)
   - Polymorphic to_dict() and from_dict() methods for JSON serialization
   - Type-safe design with comprehensive docstrings

2. **src/models/__init__.py**
   - Exported MemoryEntry, ResultEntry, ErrorEntry, and _reset_id_counter()

3. **src/services/calculator_service.py**
   - Added perform_with_memory() method that captures both successes and errors
   - Added get_memory_history() to retrieve MemoryEntry list
   - Preserved existing perform() and get_history() for backward compatibility
   - Error handling creates ErrorEntry with exception message

4. **src/storage/json_storage.py**
   - Added save_memory(entry) method for saving MemoryEntry objects
   - Added load_memory_all() method for retrieving all MemoryEntry records
   - Separate calculations_memory.json file for memory entries
   - Polymorphic handling of ResultEntry and ErrorEntry

5. **src/cli/calculator_cli.py**
   - Added show_memory_history_command() for one-shot memory history export
   - Added show_memory_history() menu option (option 9)
   - Added show_history_command() for one-shot calculation history export
   - Menu display handles both ResultEntry and ErrorEntry formatting

6. **src/__main__.py**
   - Added --memory-history flag to display memory entry history
   - Added --history flag to display calculation history
   - Updated help text and usage strings

7. **tests/test_memory_entry.py** (NEW)
   - 26 tests for ResultEntry and ErrorEntry creation and serialization
   - Tests for polymorphic deserialization, ID sequencing, field validation

8. **tests/test_calculator_service_memory.py** (NEW)
   - 11 tests for perform_with_memory() method
   - Tests for error capture, sequential IDs, execution time tracking

9. **tests/test_json_storage_memory.py** (NEW)
   - 13 tests for memory entry storage and retrieval
   - Tests for persistence, file separation, JSON format validation

10. **tests/test_integration.py** (NEW)
    - 10 integration tests for full workflow
    - Tests for coexistence of old/new systems, mixed success/error scenarios

11. **tests/test_cli.py**
    - Updated menu option numbers for new menu structure

### Test Results

- Total tests: 98
- Passed: 98
- Failed: 0
- Status: ✅ All tests pass

### Acceptance Criteria Met

- ✅ MemoryEntry stores: operation, operands, result, success/error state, timestamp, execution_time_ms, unique entry_id
- ✅ Both successful and failed calculations representable (ResultEntry/ErrorEntry subclasses)
- ✅ JSON serialization/deserialization support (to_dict/from_dict methods)
- ✅ Unique identifier per entry (counter-based sequential IDs)
- ✅ No presentation/formatting logic in class (formatting handled in CLI layer)
- ✅ Existing history preserved (backward compatible with separate calculations.json and calculations_memory.json)
- ✅ Accessible via python -m src:
  - Interactive menu: option 9 for memory history, option 10 for calculation history
  - One-shot CLI: --memory-history and --history flags
  - Help shows all available commands: python -m src --help

### Diagrams Updated

- **class_diagram.puml**: Added MemoryEntry, ResultEntry, ErrorEntry classes with inheritance relationships
- **sequence_diagram.puml**: Added MemoryEntry creation and save_memory() flow alongside CalculationResult

Duration: 617.2s | Cost: $1.223649 USD | Turns: 31
