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

## Task 04

**Description:** Create a `MemoryService` that handles storing and retrieving `MemoryEntry` objects, so that memory management is in one place and not scattered through the calculation flow.

**Status:** ✅ Complete

### Broadcast Evaluation

**Candidate A:**
- Approach: Dedicated MemoryService with store/retrieve, factory method _build_memory_service(), CLI flags --memory-retrieve and --memory-store, separate test file for MemoryService
- Test Result: 111/111 tests passed
- Key features: Clean delegation to JsonStorage, comprehensive CLI integration

**Candidate B:**
- Approach: Lightweight facade pattern with explicit delegation, --memory-retrieve flag and --memory-store with --result/--error modifiers, 5 new CLI command tests
- Test Result: 111/111 tests passed
- Key features: Flexible storage options, clear CLI semantics

**Candidate C:**
- Approach: Dedicated service layer pattern with clean separation of concerns, MemoryService as in-memory manager delegating to JsonStorage, 18 new tests covering unit and integration scenarios
- Test Result: 115/115 tests passed ✅
- Key features: Comprehensive test coverage, strongest abstraction boundaries, 17 new tests added

**Winner:** Candidate C (115/115 tests passed - highest coverage with best separation of concerns)

### Files Changed

1. **src/services/memory_service.py** (NEW)
   - MemoryService class with store(entry: MemoryEntry) → None
   - retrieve() → list[MemoryEntry] method
   - Delegates all persistence to JsonStorage
   - No business logic, pure lifecycle management

2. **src/services/__init__.py**
   - Exported MemoryService for public API

3. **src/__main__.py**
   - Added _build_memory_service() factory function
   - Instantiate and inject MemoryService to CalculatorCLI
   - Added CLI flags:
     - `--memory-retrieve`: Display all memory entries (one-shot)
     - `--memory-store OP`: Store a memory entry
     - `--result R`: Result value (with --memory-store)
     - `--error MSG`: Error message (with --memory-store)

4. **src/cli/calculator_cli.py**
   - Added memory_service parameter to __init__()
   - memory_retrieve_command() for one-shot retrieval
   - memory_store_command() for storing entries with result or error

5. **tests/test_memory_service.py** (NEW)
   - 8 unit tests for MemoryService store() and retrieve() delegation

6. **tests/test_cli.py**
   - Updated _make_cli() helper to pass memory_service mock
   - Added 5 new tests for memory CLI commands (memory_retrieve, memory_store)

7. **tests/test_integration.py** (NEW)
   - Added 4 new MemoryService integration tests
   - Tests for persistence across instances, entry type preservation

### Diagrams Updated

- **class_diagram.puml**: Added MemoryService class with store() and retrieve() methods, updated relationships
- **component_diagram.puml**: Added MemoryService component, shows it uses JsonStorage, CalculatorCLI now depends on both services
- **sequence_diagram.puml**: Added interaction flows for memory store/retrieve operations alongside calculation flows

### Test Results

- Total tests: 115
- Passed: 115
- Failed: 0
- Status: ✅ All tests pass (17 new tests added: 8 unit + 5 CLI + 4 integration)

### Acceptance Criteria Met

- ✅ MemoryService provides store(entry) and retrieve() operations
- ✅ Every completed calculation is recorded via the service
- ✅ Persistence details (file I/O, JSON) NOT inside MemoryService — delegated to JsonStorage
- ✅ Service's responsibilities limited to MemoryEntry lifecycle, no business logic
- ✅ Accessible via python -m src:
  - Interactive menu: option to view memory history
  - One-shot flags: --memory-retrieve, --memory-store OP [--result R | --error MSG]
  - Help shows all operations: python -m src --help

### Architecture Improvements

- **Clear Separation**: MemoryService handles lifecycle, JsonStorage handles persistence
- **Delegated Persistence**: All save/load operations delegated to storage layer
- **Focused Responsibility**: Service does not own business logic, only MemoryEntry management
- **CLI Exposure**: Both interactive menu and one-shot flags for all operations
- **Type Safety**: Proper handling of ResultEntry and ErrorEntry polymorphism

Duration: 159.90s | Cost: 1.7519339999999994 USD | Turns: 31

## Task 05

**Description:** Add filtering capability for stored calculations by operation type and result state.

**Status:** ✅ Complete

### Broadcast Evaluation

**Candidate A:**
- Approach: Separate FilterService with static methods, basic CLI integration, 17 new filter tests
- Test Result: 126/132 passed (6 TestRunInteractive tests failed due to menu index changes)
- Key features: Dedicated filter service, clean separation of concerns

**Candidate B:**
- Approach: FilterService with integration into MemoryService, comprehensive test suite (53 new tests), proper menu integration with all tests passing
- Test Result: 168/168 tests passed ✅
- Key features: Strong service integration, extensive test coverage (22 FilterService + 14 MemoryService filter + 17 CLI filter tests), all tests pass

**Candidate C:**
- Approach: FilterService with static method, retrieve_filtered() in MemoryService, menu option at position 10
- Test Result: 137/168 tests passed (31 tests failed - retrieve_filtered method missing)
- Key features: Attempted static method pattern but implementation incomplete

**Winner:** Candidate B (168/168 tests passed - highest test count with full implementation)

### Files Changed

1. **src/services/filter_service.py** (NEW)
   - FilterService class for in-memory filtering
   - filter_entries(entries, operation, state) method supporting filtering by operation type and/or result state
   - get_valid_operations(entries) method returns sorted list of unique operations in storage
   - Validates state parameter ('success', 'error')
   - Case-insensitive filtering for operations and states

2. **src/services/memory_service.py** (MODIFIED)
   - Added FilterService integration via dependency injection
   - Added filter_entries(operation, state) method for filtering stored entries
   - Added get_valid_operations() method to list available operations
   - Maintains separation of concerns: filtering delegated to FilterService

3. **src/cli/calculator_cli.py** (MODIFIED)
   - Added filter_command(operation, state) for one-shot CLI mode
   - Added _filter_interactive() for interactive filtering with input validation
   - Updated run_interactive() to include filter menu option (option 11)
   - Added filter validation with prompts for operation and state selection

4. **src/__main__.py** (MODIFIED)
   - Added CLI flags: --filter-op and --filter-state
   - Both flags support combined filtering (e.g., --filter-op add --filter-state success)
   - Updated argparse help text to document new flags

5. **tests/test_filter_service.py** (NEW)
   - 22 comprehensive tests for FilterService
   - Tests cover filtering by operation, result state, and combinations
   - Edge cases: empty lists, invalid states, no matches, case-insensitivity

6. **tests/test_memory_service_filter.py** (NEW)
   - 14 integration tests for MemoryService filter methods
   - Tests persistence, reload scenarios, complex filtering

7. **tests/test_cli_filter.py** (NEW)
   - 17 tests for CLI filtering functionality
   - Tests one-shot mode and interactive menu integration
   - Tests error handling and validation

8. **tests/test_cli.py** (MODIFIED)
   - Updated exit option index from 11 to 12 (filter is now option 11)
   - Updated history option index from 10 to 11

### Test Results

- Total tests: 168
- Passed: 168
- Failed: 0
- Status: ✅ All tests pass (115 existing + 53 new filter tests)

### Acceptance Criteria Met

- ✅ Programmatic filtering capability available over stored calculations
- ✅ Filtering by operation type supported (case-insensitive)
- ✅ Filtering by result state (success vs. error) supported
- ✅ Multiple filters can be combined in a single query
- ✅ Results returned as MemoryEntry objects (ResultEntry or ErrorEntry)
- ✅ Result structure consistent across all queries
- ✅ No database or external indexing system used (pure in-memory filtering)
- ✅ Accessible via python -m src:
  - Interactive menu option 11: Filter calculations with validation prompts
  - One-shot CLI: python -m src --filter-op add --filter-state success
  - Help shows all flags: python -m src --help

### Usage Examples

**Interactive Mode:**
```bash
python -m src
# Select option 11 from menu
# Enter operation type (e.g., 'add') or leave blank for all
# Enter result state (success/error) or leave blank for all
```

**One-shot Mode:**
```bash
python -m src --filter-op add              # Filter by operation only
python -m src --filter-state success       # Filter by state only
python -m src --filter-op add --filter-state success  # Combined filter
```

### Diagrams Updated

- **class_diagram.puml**: Added FilterService with filter_entries() and get_valid_operations() methods
- **component_diagram.puml**: Added FilterService component with relationships to MemoryService
- **activity_diagram.puml**: Added filter flow to interactive menu with criteria input and result display
- **sequence_diagram.puml**: Added filter flow showing CLI → MemoryService → FilterService → JsonStorage chain
- **use_case_diagram.puml**: Added "Filter entries" use case connected to User actor
- **state_diagram_interactive.puml**: Added FilterInput and FilterApply states with transitions

### Architecture Improvements

- **Focused Filtering Service**: FilterService provides pure filtering logic independent of storage
- **Service Integration**: MemoryService delegates to FilterService, maintaining clean interfaces
- **Validation**: Input validation for operation types and result states
- **Flexibility**: Support for individual filters or combined queries
- **No External Dependencies**: Pure in-memory filtering using Python list comprehensions

Duration: 631.1s | Cost: $1.274107 USD | Turns: 31

## Task 06

**Description:** Create a structured statistics component derived from stored calculations, providing programmatic access to usage and error metrics.

**Status:** ✅ Complete

### Broadcast Evaluation

All three candidates implemented identical solutions with the same structure and approach:

**Candidate A, B, and C:**
- Approach: Created Statistics dataclass with operation_counts, total_errors, error_rate_percentage, average_execution_time_ms. Created StatisticsService that computes statistics from stored MemoryEntry objects. Integrated into CLI with menu option and --statistics flag.
- Test Result: 179/185 passed (6 test_cli.py failures due to hardcoded menu option numbers needing update from 12 to 13)
- Key features: Proper separation of concerns, structured output, comprehensive test coverage

**Winner:** Candidate A (first to complete, identical implementations tied at 179 passing tests before test fixes)

### Files Changed

1. **src/models/statistics.py** (NEW)
   - Statistics dataclass with fields:
     - operation_counts: dict[str, int] (count per operation type)
     - total_errors: int (total failed operations)
     - error_rate_percentage: float (errors as percentage of total)
     - average_execution_time_ms: float (mean execution time across all operations)

2. **src/models/__init__.py** (MODIFIED)
   - Added Statistics to exports

3. **src/services/statistics_service.py** (NEW)
   - StatisticsService class that:
     - Takes MemoryService as dependency
     - compute_statistics() → Statistics method
     - Derives all metrics from stored MemoryEntry objects
     - Returns Statistics with zero values when no entries exist

4. **src/services/__init__.py** (MODIFIED)
   - Added StatisticsService to exports

5. **src/cli/calculator_cli.py** (MODIFIED)
   - Added StatisticsService initialization in __init__()
   - Added statistics_command() for one-shot mode
   - Added _show_statistics() for interactive menu display
   - Added _print_statistics_output() to format statistics for display
   - Updated run_interactive() to handle statistics menu option (option 12)
   - Updated _print_menu() to show "View statistics" as option 12

6. **src/__main__.py** (MODIFIED)
   - Added import of StatisticsService
   - Added --statistics CLI flag with help text
   - Added handler to call cli.statistics_command() when flag used

7. **tests/test_statistics_service.py** (NEW)
   - 11 comprehensive unit tests for StatisticsService
   - Tests: empty entries, single entry, mixed entries, operation counting, error rate calculation, execution time averaging, consistency, structured output

8. **tests/test_statistics_integration.py** (NEW)
   - 6 integration tests verifying statistics work with real storage
   - Tests: stored entries, calculator service integration, CLI integration, empty memory, state reflection, multiple operations

9. **tests/test_cli.py** (MODIFIED)
   - Updated hardcoded menu option numbers from 12 (exit) to 13 (exit)
   - Updated test_exit_choice, test_add_operation, test_invalid_choice_retries, test_invalid_number_retries, test_history_empty, test_history_shows_entries

### Test Results

- Total tests: 185
- Passed: 185
- Failed: 0
- Status: ✅ All tests pass (17 new tests added: 11 unit + 6 integration)

### Acceptance Criteria Met

- ✅ Statistics component/service is introduced (StatisticsService)
- ✅ Report includes:
  - count per operation type (dict mapping operation names to counts)
  - total number of errors (integer)
  - error rate as a percentage (float, 0.0-100.0)
  - average execution_time_ms (float)
- ✅ All statistics derived exclusively from stored MemoryEntry data
- ✅ Result returned as structured Statistics dataclass, not plain dictionary
- ✅ Structure of statistics output is consistent across calls (guaranteed by dataclass)
- ✅ No visualisation layer introduced (text-based console output only)
- ✅ All new functionality accessible via python -m src:
  - Interactive menu option 12: "View statistics"
  - One-shot CLI flag: python -m src --statistics
  - Help shows flag: python -m src --help

### Usage Examples

**Interactive Mode:**
```bash
python -m src
# Select option 12 from menu to view statistics
```

**One-shot Mode:**
```bash
python -m src --statistics
```

**Output Format:**
```
=== Statistics ===

  Operation Counts:
    add: 5
    divide: 2
    
  Total errors: 1
  Error rate: 16.67%
  Average execution time: 1.25ms
```

### Diagrams Updated

All PlantUML diagrams in artifacts/ updated to reflect Statistics component:
- **class_diagram.puml**: Added Statistics dataclass and StatisticsService with relationships
- **component_diagram.puml**: Added Statistics Service component with dependencies
- **use_case_diagram.puml**: Added "View statistics" use case
- **activity_diagram.puml**: Added statistics case to interactive menu
- **sequence_diagram.puml**: Added Statistics Flow showing CLI → Service → Memory → Storage
- **state_diagram_interactive.puml**: Added StatsDisplay state with transitions

Duration: 772.2s | Cost: $1.740668 USD | Turns: 74
