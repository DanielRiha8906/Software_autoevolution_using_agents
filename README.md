# Autoevoluce softwaru pomocí autonomních agentů řízených velkým jazykovým modelem

> Bachelor thesis repository

This repository contains the practical implementation accompanying the bachelor thesis **"Autoevoluce softwaru pomocí autonomních agentů řízených velkým jazykovým modelem"** (Software Auto-Evolution Using Autonomous Agents Driven by a Large Language Model).

---

## About

The thesis explores whether a large language model (LLM), acting as an autonomous software agent, can independently evolve and maintain a software project — writing code, fixing bugs, extending functionality, and managing workflows — with minimal human intervention.

The central hypothesis is that modern LLMs, when equipped with the right tooling and autonomy, are capable of closing the feedback loop between software specification, implementation, testing, and deployment without requiring a human developer at every step.

---

## Applications

### `baseline/calculator`

A Python OOP calculator with persistent history, an interactive CLI menu, and one-shot command mode. It serves as the primary **baseline application** on which the autonomous agent is evaluated. The calculator is intentionally kept simple and well-structured (models, services, storage, CLI layers) so that agent-driven evolution can be measured clearly — new operations, refactors, test coverage improvements, or architecture changes introduced by the agent are traceable against a known starting point.

### `baseline/TODO`

A Python CLI task manager (to-do list) with JSON persistence, status tracking, and an interactive menu. It acts as a **second baseline**, offering a different domain and slightly richer state model than the calculator. Having two baselines allows the thesis to assess whether the agent's evolution capabilities generalise across problem types or are sensitive to the specific application structure.

### `github-workflow-manager` *(placeholder — see below)*

A tool for orchestrating GitHub Actions workflows from within the autonomous agent loop, enabling the agent to trigger CI runs, monitor results, and react to failures as part of its self-improvement cycle.

---

## Structure

```
baseline/
├── calculator/          OOP calculator baseline
└── TODO/                CLI task manager baseline

github-workflow-manager/ GitHub workflow orchestration tool (WIP)
```

---

## Author

Daniel Ova — bachelor thesis, 2026
