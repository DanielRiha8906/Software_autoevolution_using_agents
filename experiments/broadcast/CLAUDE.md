# Architecture: Broadcast (Fan-out)

All agents receive the same task input simultaneously and work in parallel. No agent waits for another's output before starting. The orchestrator collects all outputs after all agents finish.

## Orchestrator responsibilities

1. Distribute the task input to all relevant agents at the same time.
2. Wait for all outputs.
3. Synthesize: integrate the outputs and resolve any conflicts between agent reports.
4. Produce a single combined result for the step.

## Communication rules

- Agents do not see each other's output during the same step.
- Each agent reads only the current project files and the task input you provide.
- No agent output may be used as input to another agent within the same step.
- If two agents produce contradictory outputs, the orchestrator resolves it — do not re-invoke agents.
