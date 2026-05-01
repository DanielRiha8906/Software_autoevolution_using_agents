# Calculator

OOP calculator with persistent history, interactive menu, and one-shot CLI mode.

## Requirements

- Python 3.12+
- `pytest` (tests only)
- `plantuml` (diagrams only)

## Running

**Interactive menu**
```bash
cd baka/third/calculator
python -m src
```

**One-shot command**
```bash
python -m src --operation add 3 5
python -m src --operation subtract 10 4
python -m src --operation multiply 6 7
python -m src --operation divide 10 3
```

Operations: `add` `subtract` `multiply` `divide`

## Tests

```bash
pytest tests/
pytest tests/ -v        # verbose
pytest tests/ -k calc   # filter by name
```

## Diagrams

```bash
./generate_diagrams.sh          # PNG (default)
./generate_diagrams.sh svg
./generate_diagrams.sh pdf
```

Output is written to `artifacts/`.

## Structure

```
src/
├── __main__.py          entry point, argument parsing
├── models/
│   ├── operation.py     Operation enum (add / subtract / multiply / divide)
│   └── calculation_result.py  result dataclass with timestamp
├── services/
│   ├── calculator.py    core arithmetic, division-by-zero guard
│   └── calculator_service.py  orchestrates calculation and persistence
├── storage/
│   └── json_storage.py  reads and writes artifacts/calculations.json
└── cli/
    └── calculator_cli.py  interactive menu and command mode output

tests/                   pytest test suite (38 tests)
artifacts/               generated diagrams and calculations.json
```
