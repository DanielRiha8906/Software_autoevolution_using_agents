# Task 05 Design: MemoryService Query Method

## Method Signature

```python
def query(self, operation: Optional[str] = None, success: Optional[bool] = None) -> list[MemoryEntry]:
    """Filter stored entries by operation type and/or success state.
    
    Enables querying the in-memory entry collection using optional filters on
    operation type and success state. Filters combine with AND logic: if both
    parameters are provided, results must match both conditions.
    
    Args:
        operation: Optional operation type filter (e.g., "add", "multiply").
                   Performs case-sensitive exact string matching.
                   None means no filter on operation.
        success: Optional success state filter (True or False).
                 Performs exact boolean matching.
                 None means no filter on success state.
    
    Returns:
        list[MemoryEntry]: List of entries matching ALL provided filters.
                          Returns empty list if no matches found.
                          Returns copy of all entries if both parameters are None.
                          Preserves insertion order from internal _entries list.
    
    Filter Logic (AND Combination):
    - Both parameters None → return all entries (same as retrieve())
    - operation only → return entries where entry.operation == operation
    - success only → return entries where entry.success == success
    - both provided → return entries where BOTH conditions match
    
    Example:
        service.query()                    # all entries
        service.query(operation="add")     # entries with "add" operations
        service.query(success=True)        # successful entries
        service.query(operation="multiply", success=False)  # failed multiply ops
    """
```

## Import Requirements

File: `src/services/memory_service.py`

Add to existing imports:
```python
from typing import Optional
```

## Filtering Algorithm

**Pseudocode:**

```
function query(operation: Optional[str], success: Optional[bool]) -> list[MemoryEntry]:
    result = []
    
    for each entry in self._entries:
        matches = True
        
        // If operation filter is provided, check if entry.operation matches
        if operation is not None:
            if entry.operation != operation:
                matches = False
        
        // If success filter is provided, check if entry.success matches
        if success is not None:
            if entry.success != success:
                matches = False
        
        // Add to result if ALL active filters matched
        if matches:
            result.append(entry)
    
    return result
```

**Implementation Approach (List Comprehension - Recommended):**
```python
def query(self, operation: Optional[str] = None, success: Optional[bool] = None) -> list[MemoryEntry]:
    return [
        entry for entry in self._entries
        if (operation is None or entry.operation == operation)
        and (success is None or entry.success == success)
    ]
```

## Edge Cases Handled

1. **Both parameters None** → Return all entries
2. **Empty service** → Return empty list
3. **No matches for operation** → Return empty list
4. **No matches for success** → Return empty list
5. **No matches for combined filters** → Return empty list
6. **Case sensitivity** → "Add" != "add" (exact string matching)
7. **Partial matches rejected** → "ad" != "add" (exact match only)

## Integration with Existing Code

**Dependencies:**
- Imports `MemoryEntry` from `src.models.memory_entry` (already imported in class)
- Uses `self._entries` (existing private attribute)
- Return type `list[MemoryEntry]` matches existing `retrieve()` return type

**No changes needed to:**
- MemoryEntry model (already has operation and success fields)
- Any other service or class
- Constructor or initialization logic
- Existing store() and retrieve() methods

## Implementation Checklist for Programmer

1. Add import: `from typing import Optional`
2. Add `query` method to MemoryService class with:
   - Proper method signature with type hints
   - Comprehensive docstring
   - List comprehension implementation or explicit loop
3. Verify no file I/O in method
4. Ensure type hints are correct throughout
5. No modification to existing methods
