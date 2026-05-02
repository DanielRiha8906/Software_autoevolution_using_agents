# Experiment Governance

## Agents (defined in .claude/agents/)

| Agent | Role | Writes to |
|---|---|---|
| data-analyst | Analyze requirements and code, produce a structured report | nothing |
| system-architect | Design file-level plan and test specs | nothing |
| python-programmer | Implement the design | src/ |
| pytest-tester | Write and run tests, escalate production bugs | tests/ |
| uml-designer | Create/update PlantUML diagrams | artifacts/ |

## Hard limits

- **Never read or write to `baseline/`** — it is the unmodified reference copy.
- **Never read or write outside your experiment folder** — each experiment is isolated.
- **Never modify `CLAUDE.md` files, `prompts/`, or `.claude/agents/`** — governance files.
- **Do not install packages** unless the task explicitly requires a new dependency.

## Runtime & CLI Exposure Requirements

- **All functionality must be reachable via `python -m src`** — a feature is not complete until it has a CLI entry point.
- **No internal-only implementations** — a service that exists only as a class with no `__main__.py` wiring is incomplete.
- **Add the command/flag** to the `argparse` parser in `src/__main__.py`.
- **Support both modes** — interactive (menu option) and one-shot (flag + args), matching the style of existing commands.
- **`python -m src --help` must list every supported operation.**
- **`python -m src` must not raise unhandled exceptions on valid inputs.**
- **GUI and purely graphical features are exempt from the one-shot flag requirement** — a feature that only makes sense in a windowed interface does not need a CLI flag. The interactive menu entry is still required.