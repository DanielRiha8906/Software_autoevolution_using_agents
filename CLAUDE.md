# Experiment Root

This repository runs 27 autonomous autoevolution experiments across 3 MAS architectures, 3 prompt strategies, and 3 baseline projects.

## Structure

- `baseline/` — original unmodified projects (calculator, TODO, github-workflow-manager). Never modify these.
- `experiments/<architecture>/<strategy>/<project>/` — working copy for each experiment run
- `prompts/architectures/` — system prompts per architecture
- `prompts/strategies/` — task input format per strategy
- `results/` — evaluation outputs

## Baseline projects

- `baseline/calculator/`
- `baseline/TODO/`
- `baseline/github-workflow-manager/`

## How experiments run

Each experiment copies the relevant baseline into its folder and runs the autoevolution pipeline (rows 1-10) autonomously. No human intervention during a run.
