# Progress Log

## Task 01: Add execution_time_ms tracking to CalculationResult

**Objective:** Add automatic execution time measurement to calculation results for performance profiling.

**Acceptance Criteria:** ✅ All met
- `CalculationResult` has an `execution_time_ms` attribute representing elapsed time in milliseconds
- The attribute is populated automatically for every calculation — no manual input required
- Measurement uses only the standard library (no third-party timing packages)
- Existing code that constructs or reads `CalculationResult` continues to work without changes

**Files Changed:**
- `src/models/calculation_result.py` — Added `execution_time_ms: float` field with default 0.0; updated `from_dict()` for backward compatibility
- `src/services/calculator_service.py` — Added timing measurement using `time.perf_counter()` around calculation
- `tests/test_calculator_service.py` — Enhanced 5 existing tests with execution_time_ms assertions; added 2 new tests
- `tests/test_json_storage.py` — Enhanced 1 existing test; added 2 new backward-compatibility tests
- `artifacts/class_diagram.puml` — Added `executionTimeMs : float` field to CalculationResult class
- `artifacts/activity_diagram.puml` — Added timing measurement steps to flow diagram

**Test Results:**
- Total tests: 42
- Passed: 42 ✅
- Failed: 0
- Coverage: All operation types (ADD, SUBTRACT, MULTIPLY, DIVIDE) verified to measure execution time

**Implementation Notes:**
- Timing measures only Calculator.calculate() work, excludes JSON storage I/O
- Uses `time.perf_counter()` for high-precision wall-clock measurement
- Default value of 0.0 allows graceful loading of old JSON records without execution_time_ms
- No breaking changes to API; all existing code continues to work

Duration: 220.3s | Cost: $0.388252 USD | Turns: 13

## Task 02: Add square, sqrt, power, and modulo operations

**Objective:** Extend the calculator with advanced mathematical operations (square, sqrt, power, modulo) to enable more comprehensive calculations without switching tools.

**Acceptance Criteria:** ✅ All met
- Operations implemented: `square(x)`, `sqrt(x)`, `power(x, y)`, `modulo(x, y)`
- Each operation follows the same interface as existing operations (add, subtract, etc.)
- `sqrt` of a negative number raises an error
- `modulo` by zero raises an error
- `power` with negative or fractional exponents returns correct results
- No existing operations duplicated or renamed
- All operations accessible via `python -m src` (menu and CLI flag)

**Files Changed:**
- `src/models/operation.py` — Added SQUARE, SQRT, POWER, MODULO enum members
- `src/services/calculator.py` — Added 4 new methods (square, sqrt, power, modulo) with proper error handling; updated calculate() dispatch dict; imported math module
- `src/models/calculation_result.py` — Updated _SYMBOLS dict with symbols for new operations (sq, √, ^, %)
- `src/cli/calculator_cli.py` — Added 4 menu entries to _MENU tuple (Square, Sqrt, Power, Modulo)
- `src/__main__.py` — Updated argparse choices to include all 8 operations; updated usage string
- `tests/test_calculator.py` — Added 25 new tests (TestSquare, TestSqrt, TestPower, TestModulo classes)
- `tests/test_calculator_service.py` — Added 20 new integration tests for service layer
- `tests/test_cli.py` — Added 12 new CLI tests; updated 6 existing tests for menu position changes
- `artifacts/class_diagram.puml` — Updated Operation enum (8 members) and Calculator class (9 methods)

**Test Results:**
- Total tests: 99
- Passed: 99 ✅
- Failed: 0
- Execution time: 0.15s
- Coverage: All operations, error conditions, service integration, CLI behavior, and persistence verified

**Implementation Notes:**
- Error handling: sqrt raises ValueError for negative numbers; modulo raises ValueError for zero divisor; power raises ValueError for zero base with negative exponent
- Unary operations (square, sqrt) modeled as binary for consistency with existing CalculationResult model
- Display symbols: square="sq", sqrt="√", power="^", modulo="%"
- All operations integrated with CalculatorService for automatic persistence and execution time tracking
- No breaking changes; all existing operations remain unchanged
- Interactive menu expanded to 8 operations (positions 1-8), history at position 9, exit at position 10

Duration: 427.1s | Cost: $0.703650 USD | Turns: 15

## Task 03: Create MemoryEntry class for history data structure

**Objective:** Implement a dedicated `MemoryEntry` class that captures complete history of both successful and failed calculations, enabling consistent history data structure for querying and reporting.

**Acceptance Criteria:** ✅ All met
- `MemoryEntry` stores: operation name, input operands, result, success/error state, execution timestamp, and `execution_time_ms`
- Both successful and failed calculations can be represented
- `MemoryEntry` can be serialised to and deserialised from a JSON-compatible dictionary
- Each entry has a unique identifier
- Presentation/formatting logic is kept out of the class
- Existing calculation history is not broken
- All new functionality accessible via `python -m src` — both as interactive menu option and one-shot CLI flag

**Files Changed:**
- `src/models/memory_entry.py` — Created MemoryEntry dataclass with 9 fields (entry_id, operation_name, operand_a, operand_b, result, success, error_message, timestamp, execution_time_ms); auto-generates UUID4 entry_id and ISO timestamp; implements to_dict() and from_dict() without presentation logic
- `src/services/memory_service.py` — Created MemoryService class that orchestrates calculation execution with timing, error handling, and MemoryEntry creation; includes record() and get_all_entries() methods
- `src/storage/json_storage.py` — Updated to handle both CalculationResult and MemoryEntry types; modified deserialization to distinguish by 'entry_id' key; maintains backward compatibility
- `src/cli/calculator_cli.py` — Added show_memory_cli() for one-shot display; added _show_memory() for interactive menu; updated menu to include memory option (position 10); updated run_interactive() to handle memory choice
- `src/__main__.py` — Updated _build_service() to instantiate MemoryService alongside CalculatorService; added --memory flag to argument parser; added logic to display memory entries when --memory flag provided
- `src/services/calculator_service.py` — Updated get_history() to filter CalculationResult instances when loading mixed storage
- `tests/test_memory_entry.py` — Created 27 tests covering MemoryEntry creation, unique IDs, timestamp format, serialization round-trips, execution_time_ms handling, and verification of no custom formatting logic
- `tests/test_memory_service.py` — Created 33 tests covering initialization, successful calculations (all 8 operations), failed calculations, execution time tracking, storage persistence, entry retrieval, and operation validation
- `tests/test_memory_storage.py` — Created 16 tests covering save/load round-trips, failed entry persistence, multiple entry accumulation, type detection, backward compatibility with CalculationResult, and mixed storage
- `tests/test_memory_cli_integration.py` — Created 18 tests covering show_memory_cli() with empty/single/multiple entries, failed entry display, --memory flag integration, and interactive menu option
- `tests/test_cli.py` — Updated 12 existing tests to account for menu position shifts (exit option moved from 10 to 11)
- `artifacts/class_diagram.puml` — Added MemoryEntry model class and MemoryService service class with relationships
- `artifacts/component_diagram.puml` — Added MemoryService component and updated dependencies
- `artifacts/activity_diagram.puml` — Added memory recording flows for both successful and failed calculations
- `artifacts/use_case_diagram.puml` — Added "View memory entries" use case
- `artifacts/state_diagram_interactive.puml` — Added MemoryDisplay and MemoryRecord states
- `artifacts/state_diagram_command.puml` — Added MemoryRecorded state

**Test Results:**
- Total tests: 193
- Passed: 193 ✅
- Failed: 0
- New tests written: 94 (27 + 33 + 16 + 18)
- Existing tests updated: 12 (menu position shifts)
- Execution time: 0.42s
- Coverage: MemoryEntry creation/serialization, MemoryService orchestration, mixed type storage, backward compatibility, CLI integration, and error handling all verified

**Implementation Notes:**
- UUID4 format for entry_id: `uuid.uuid4().hex` produces 32-character hex string (no hyphens)
- Timestamp format: ISO 8601 via `datetime.now().isoformat()`, consistent with CalculationResult
- Error handling: MemoryService catches all exceptions during calculation and records them with success=False, error_message=str(exception), result=None
- Storage polymorphism: Both CalculationResult and MemoryEntry objects coexist in same JSON file; deserialization detects type by presence of 'entry_id' key
- MemoryEntry has no custom __str__() or __repr__() — presentation logic remains in CLI layer only
- Backward compatibility: Old CalculationResult entries load as CalculationResult; new entries load as MemoryEntry; both types accessible via same API
- CLI integration: Menu option 10 displays memory, option 11 exits; --memory flag prints all memory entries; both modes work without history data
- No breaking changes to existing CalculationResult or CalculatorService APIs

Duration: 578.3s | Cost: $1.043396 USD | Turns: 27

## Task 04: Implement MemoryService for history management

**Objective:** Implement a `MemoryService` that handles storing and retrieving `MemoryEntry` objects, consolidating memory management in one place instead of scattering it through the calculation flow.

**Acceptance Criteria:** ✅ All met
- `MemoryService` provides `store(entry)` and `retrieve()` operations (via `record()` and `get_all_entries()`)
- Every completed calculation (success or failure) is recorded via the service
- Persistence details (file I/O, serialisation) are not inside `MemoryService` — they live in JsonStorage
- The service's responsibilities are limited to `MemoryEntry` lifecycle; it does not own business logic
- All new functionality is accessible via `python -m src` — both as interactive menu option and one-shot CLI flag

**Files Changed:**
- (No new files created; implementation completed in Task 03)
- `src/services/memory_service.py` — Verified complete implementation with `record()` and `get_all_entries()` methods
- `src/models/memory_entry.py` — Verified complete dataclass with all 9 fields and serialization
- `src/storage/json_storage.py` — Verified polymorphic storage supporting both CalculationResult and MemoryEntry
- `src/cli/calculator_cli.py` — Verified integration with memory display functionality
- `src/__main__.py` — Verified --memory flag and menu integration

**Test Results:**
- Total tests: 193
- Passed: 193 ✅
- Failed: 0
- Execution time: 0.29s
- Coverage: All MemoryService functionality verified by test suite (tests covering record(), get_all_entries(), error handling, persistence, and CLI integration)

**Implementation Notes:**
- `MemoryService.record(operation, operandA, operandB)` combines entry creation and storage (equivalent to store() operation)
- `MemoryService.get_all_entries()` retrieves persisted entries (equivalent to retrieve() operation)
- Service uses JsonStorage for persistence, keeping I/O logic separate
- Supports both successful and failed calculation recording
- Error handling catches all exceptions and records them with success=False
- Execution time automatically measured and stored with each entry
- Service integrated into CLI with --memory flag and interactive menu option (position 10)
- No breaking changes to existing CalculationService or storage APIs
- Backward compatible with CalculationResult legacy format

Duration: 153.5s | Cost: $0.324552 USD | Turns: 17

## Task 05: Filter stored calculations by operation type and result state

**Objective:** Implement filtering capability for memory entries, allowing users to retrieve and reuse relevant past results by filtering on operation type and success/error state.

**Acceptance Criteria:** ✅ All met
- Programmatic filtering capability is available over stored calculations
- Filtering by operation type is supported (case-insensitive)
- Filtering by result state (success vs. error) is supported
- Multiple filters can be combined in a single query (AND logic)
- Results are returned as a collection of `MemoryEntry` objects
- Structure of returned results is consistent across all queries
- No database or external indexing system is used (in-memory filtering)
- All new functionality is accessible via `python -m src` (both interactive menu and CLI flags)

**Files Changed:**
- `src/services/memory_service.py` — Added 3 new filtering methods: `filter_by_operation()`, `filter_by_success()`, and `filter()` (generic with AND logic for combined filters)
- `src/cli/calculator_cli.py` — Added `show_filtered_memory_cli()` for CLI output; added `_show_memory_filter_submenu()` for interactive submenu; added `_display_memory_entries()` helper; updated `_show_memory()` to call submenu
- `src/__main__.py` — Added 3 argparse arguments: `--filter-operation`, `--filter-success`, `--filter-error`; added validation (mutual exclusivity of success/error); integrated filter logic in main()
- `tests/test_memory_service.py` — Added 28 new tests covering all filter methods, edge cases (empty results, case sensitivity, combined filters), and type consistency
- `tests/test_cli.py` — Added 12 new tests for CLI flag integration, help text, and filtered output; added 10 tests for interactive submenu with all options (view all, filter by operation, by success, by error, back)
- `artifacts/class_diagram.puml` — Updated MemoryService to include new filtering methods; updated CalculatorCLI to include new filtering methods
- `artifacts/activity_diagram.puml` — Added filter submenu flow with 4 filtering options
- `artifacts/use_case_diagram.puml` — Added "Filter memory by operation" and "Filter memory by result state" use cases as extensions of "View memory entries"

**Test Results:**
- Total tests: 237
- Passed: 237 ✅
- Failed: 0
- New tests written: 50 (28 memory service + 22 CLI/integration)
- Execution time: 0.36s
- Coverage: All filter methods, edge cases, CLI flag integration, interactive menu, combined filters, and type consistency verified

**Implementation Notes:**
- Three-method filtering approach: `filter_by_operation()` and `filter_by_success()` for specific single-field filtering; generic `filter()` for combined criteria with AND logic
- Case-insensitive operation filtering (e.g., "ADD", "add", "Add" all match)
- Combined filters use AND logic: both criteria must match (intersection)
- In-memory filtering: all entries loaded from storage, then filtered in-process (no database/indexing needed)
- CLI flags: `--filter-operation` (choices hardcoded), `--filter-success` (boolean flag), `--filter-error` (boolean flag); mutual exclusivity enforced
- Interactive submenu: 5 options under "View memory entries" (option 10): View all, Filter by operation, Filter by success, Filter by error, Back
- Filtering methods return MemoryEntry objects, preserving consistency with existing APIs
- MemoryService responsible for filtering logic; CalculatorCLI responsible for display/prompting
- No breaking changes to existing MemoryService, CalculatorService, or CLI APIs
- Full backward compatibility with existing memory entries and calculation history

Duration: PENDING | Cost: PENDING | Turns: PENDING
