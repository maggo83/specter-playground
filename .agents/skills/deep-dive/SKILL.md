---
name: deep-dive
description: Comprehensive architectural investigation of a subsystem or flow with parallel analysis and mermaid diagrams. Takes a long time and many tokens. Use for documentation, architectural decisions and full dependency understanding; for a specific question use quick-dive.
argument-hint: "<area to investigate or question about the architecture>"
---

# Deep Dive

Hand the investigation to the `architecture-archaeologist` agent. Its process and output format are defined in `.agents/agents/architecture-archaeologist.md`; do not restate them here.

Agree on the area with the user before starting if it is vague, since scope drives cost. The planning pass runs on a standard or top tier, the per-track investigation on a cheap tier (see `orchestrate` for the fan-out mechanics).

Quick dive versus deep dive:

| | `quick-dive` | `deep-dive` |
|---|---|---|
| Question | specific | open-ended, architectural |
| Scope | at most 10 files | unlimited |
| Output | under 1000 words, 0 or 1 diagram | full document, several diagrams |
| Sub-agents | none | parallel tracks |
| Pick when | you need an answer now | you need to understand or document a subsystem |
