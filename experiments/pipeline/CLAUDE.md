# Architecture: Pipeline

Agents run in a fixed sequence. Each agent receives the task input plus the structured output of every preceding agent in the chain.

## Execution order

1. **data-analyst** — analyze requirements, identify scope and constraints
2. **system-architect** — design based on the analyst report
3. **python-programmer** — implement based on the design
4. **pytest-tester** — test the implementation
5. **uml-designer** — update diagrams to reflect all changes

## Orchestrator responsibilities

- Pass each agent's full output as context to the next agent.
- Do not skip steps.
- If an agent escalates a blocker (e.g., a production bug found by the tester), stop the pipeline and report which step failed and why.
- Do not loop back — invoke each agent at most once per step.
