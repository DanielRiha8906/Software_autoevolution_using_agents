# Design: MemoryEntry Class Implementation

## Overview

Implement a new `MemoryEntry` dataclass that provides comprehensive operation history tracking with unique identifiers, execution status, and error information.

## MemoryEntry Class Definition

**File:** `src/models/memory_entry.py`

```python
from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4
from typing import Optional


@dataclass
class MemoryEntry:
    """
    Comprehensive audit entry for a calculator operation attempt.
    
    Tracks both successful and failed operations with unique identifiers,
    execution status, and detailed error information.
    
    Attributes:
        entry_id (str): Unique identifier (UUID4). Can be set explicitly for testing.
        operation (str): Operation name (e.g., "add", "sqrt"). Must match Operation enum values.
        operand_a (float): First operand.
        operand_b (float): Second operand.
        result (Optional[float]): Calculation result (None if operation failed).
        success (bool): True if operation completed without error, False otherwise.
        error_message (Optional[str]): Error message if operation failed, None if successful.
        timestamp (str): ISO 8601 timestamp of operation attempt.
        execution_time_ms (float): Time taken to execute operation, in milliseconds. Default 0.0.
    """
    operation: str
    operand_a: float
    operand_b: float
    result: Optional[float]
    success: bool
    error_message: Optional[str]
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default="")
    execution_time_ms: float = 0.0

    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Serialize MemoryEntry to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """Deserialize MemoryEntry from dictionary."""
        return cls(**data)
```

## Test Specifications

**File:** `tests/test_memory_entry.py`

### Test Class 1: TestMemoryEntryCreation

| Test Name | Input | Expected Output |
|-----------|-------|-----------------|
| test_memory_entry_with_success | operation="add", operand_a=3, operand_b=5, result=8, success=True, error_message=None | MemoryEntry with all fields set correctly |
| test_memory_entry_with_failure | operation="sqrt", operand_a=-1, result=None, success=False, error_message="Square root of negative" | MemoryEntry with success=False, result=None, error_message set |
| test_memory_entry_success_true | operation="add", operand_a=1, operand_b=2, result=3, success=True | entry.success == True (type: bool) |
| test_memory_entry_success_false | operation="divide", operand_a=1, operand_b=0, result=None, success=False, error_message="Divide by zero" | entry.success == False (type: bool) |

### Test Class 2: TestMemoryEntryID

| Test Name | Input | Expected Output |
|-----------|-------|-----------------|
| test_memory_entry_has_unique_id | Create 3 separate MemoryEntry objects | All three have different entry_id values |
| test_memory_entry_id_is_uuid_string | Create MemoryEntry with default ID generation | entry_id matches UUID4 format (36-char hex with hyphens) |
| test_memory_entry_id_can_be_set_explicitly | Create MemoryEntry with entry_id="test-id-123" | entry.entry_id == "test-id-123" |
| test_memory_entry_id_is_set_on_creation | Create MemoryEntry without explicit entry_id | entry_id is auto-generated, not empty |

### Test Class 3: TestMemoryEntryTimestamp

| Test Name | Input | Expected Output |
|-----------|-------|-----------------|
| test_memory_entry_timestamp_auto_generated | Create MemoryEntry without timestamp param | timestamp is ISO format string, within 1 second of now |
| test_memory_entry_timestamp_can_be_explicit | Create MemoryEntry with timestamp="2026-05-02T10:30:00" | entry.timestamp == "2026-05-02T10:30:00" |
| test_memory_entry_timestamp_format | Create MemoryEntry with default timestamp | timestamp matches ISO 8601 format (YYYY-MM-DDTHH:MM:SS or with fractional seconds) |

### Test Class 4: TestMemoryEntrySerialization

| Test Name | Input | Expected Output |
|-----------|-------|-----------------|
| test_memory_entry_to_dict_success | MemoryEntry(operation="add", operand_a=1, operand_b=2, result=3, success=True, error_message=None, entry_id="test1", timestamp="2026-05-02T10:30:00", execution_time_ms=1.5) | dict with all 9 keys: entry_id, operation, operand_a, operand_b, result, success, error_message, timestamp, execution_time_ms |
| test_memory_entry_to_dict_failure | MemoryEntry(..., success=False, result=None, error_message="Error msg", ...) | dict with success=False, result=None, error_message="Error msg" |
| test_memory_entry_from_dict_success | dict with success=True, result=8, error_message=None, all other required fields | MemoryEntry object with correct fields |
| test_memory_entry_from_dict_failure | dict with success=False, result=None, error_message="Error", all other required fields | MemoryEntry object with error_message preserved, result=None |
| test_memory_entry_round_trip | Create entry → to_dict() → from_dict() | Resulting entry equals original (all fields match) |

### Test Class 5: TestMemoryEntryFields

| Test Name | Input | Expected Output |
|-----------|-------|-----------------|
| test_memory_entry_with_zero_operands | operand_a=0, operand_b=0 | entry.operand_a == 0, entry.operand_b == 0 |
| test_memory_entry_with_negative_operands | operand_a=-5, operand_b=-10 | entry.operand_a == -5, entry.operand_b == -10 |
| test_memory_entry_with_large_numbers | operand_a=1e100, operand_b=1e200, result=1e300 | entry stores values correctly |
| test_memory_entry_none_result_on_failure | success=False, result=None | entry.result is None |
| test_memory_entry_float_result_on_success | success=True, result=8.0 | entry.result == 8.0 (type: float) |
| test_memory_entry_execution_time_optional | Create entry without execution_time_ms param | entry.execution_time_ms == 0.0 (default) |

### Test Class 6: TestMemoryEntryFieldTypes

| Test Name | Input | Expected Output |
|-----------|-------|-----------------|
| test_memory_entry_operation_string | operation="add" | entry.operation == "add" (type: str) |
| test_memory_entry_operand_a_float | operand_a=3.5 | entry.operand_a == 3.5 (type: float) |
| test_memory_entry_operand_b_float | operand_b=2.7 | entry.operand_b == 2.7 (type: float) |
| test_memory_entry_result_optional_float | result=None or result=5.5 | entry.result is None or type float |
| test_memory_entry_success_boolean | success=True or success=False | entry.success is bool type |
| test_memory_entry_error_message_optional_string | error_message=None or error_message="msg" | entry.error_message is None or str type |
| test_memory_entry_timestamp_string | timestamp="2026-05-02T10:30:00" | entry.timestamp == "2026-05-02T10:30:00" (type: str) |
| test_memory_entry_entry_id_string | entry_id="test-id" | entry.entry_id == "test-id" (type: str) |
| test_memory_entry_execution_time_float | execution_time_ms=2.5 | entry.execution_time_ms == 2.5 (type: float) |

## Files to Create

### 1. src/models/memory_entry.py
- New dataclass MemoryEntry with 9 fields
- Implement __post_init__, to_dict(), from_dict()
- Include docstring as above
- Import: dataclasses, datetime, uuid, typing

### 2. tests/test_memory_entry.py
- 6 test classes with total of 27+ test methods
- TestMemoryEntryCreation: 4 tests
- TestMemoryEntryID: 4 tests  
- TestMemoryEntryTimestamp: 3 tests
- TestMemoryEntrySerialization: 5 tests
- TestMemoryEntryFields: 6 tests
- TestMemoryEntryFieldTypes: 9 tests (for comprehensive type coverage)

## Files NOT Modified

- src/models/calculation_result.py (unchanged)
- src/services/calculator_service.py (unchanged)
- src/storage/json_storage.py (unchanged)
- Any other existing files

## Implementation Order

1. Create src/models/memory_entry.py with MemoryEntry class
2. Create tests/test_memory_entry.py with all test cases
3. Run pytest to verify all tests pass
4. Done (no integration changes in this task)

## Key Design Decisions

1. **Unique ID:** UUID4 generated by default, can be overridden for testing
2. **Success/Error:** Boolean `success` flag + optional `error_message` field
3. **Result:** Optional[float] to support None for failed operations
4. **Timestamp:** Auto-generated in __post_init__ if not provided
5. **No Validation:** Class accepts any values, validation is upstream responsibility
6. **Backward Compatible:** New class only, doesn't modify existing code
7. **Serialization:** Standard to_dict/from_dict pattern matching CalculationResult

## Expected Test Output

All 27+ tests should pass:
- No failures
- No errors
- Full coverage of MemoryEntry class behavior
