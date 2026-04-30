# Architecture: Supervisor as Tools

The orchestrator treats agents as callable tools and decides which to invoke based on current project state. There is no fixed execution order.

## Orchestrator responsibilities

- Assess current project state before each decision.
- Select the most appropriate agent to make progress toward the step goal.
- Incorporate each agent's output into your context before deciding the next action.
- Stop when the step is complete and all acceptance criteria are met.

## Communication rules

- Agents communicate only with the orchestrator, never with each other.
- Each agent invocation is independent — always provide full context with each call.
- You may invoke agents in any order and any number of times per step.
- Do not invoke an agent when its work is already complete.
- Do not invoke an agent to redo correct work already done by another agent.
