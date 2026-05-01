Calculator — OOP Python app.
src/models/: Operation (enum), CalculationResult (dataclass)
src/services/: Calculator (arithmetic), CalculatorService (orchestrates + persists)
src/storage/: JsonStorage (artifacts/calculations.json)
src/cli/: CalculatorCLI (interactive menu + one-shot mode)
tests/: pytest (38 tests)

Edit only src/ and tests/. Tests: pytest tests/ -q
Diagrams: ./generate_diagrams.sh → artifacts/*.puml
