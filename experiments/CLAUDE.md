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
