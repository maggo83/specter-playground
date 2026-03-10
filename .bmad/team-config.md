# Team Configuration — Specter-Playground

---

## Model Assignments

The orchestrator uses this table to decide which model/provider to invoke for each agent role.
Adjust provider and model names to match whichever API keys are available in the environment.

| Agent | Model Tier | Preferred Model | Notes |
|---|---|---|---|
| orchestrator | high | claude-opus-4.X / gpt-5.1 | Complex coordination, ambiguity resolution |
| architect | high | claude-opus-4.X / gpt-5.1 | Design decisions, cross-system reasoning |
| security | high | claude-opus-4.X / gpt-5.1 | Critical — never downgrade this role |
| pm | medium | claude-sonnet-4.X / gpt-4.1-mini | Structured output, requirements |
| ux-designer | medium | claude-sonnet-4.X / gpt-4.1-mini | Screen flow, layout decisions |
| scrum-master | medium | claude-sonnet-4.X / gpt-4.1-mini | Commit/PR operations |
| developer | medium | claude-sonnet-4.X / codex | Code generation |
| micropython-specialist | medium | claude-sonnet-4.X / codex | Embedded code |
| lvgl-mockui-specialist | medium | claude-sonnet-4.X / codex | UI code + MCP tool use |
| hw-bootloader-specialist | medium | claude-sonnet-4.X / codex | C/embedded code |
| tester | medium | claude-haiku-3.X / gpt-4.1-nano | High-volume, repetitive |
| i18n-specialist | medium | claude-haiku-3.X / gpt-4.1-nano | Structured text tasks |
| doc-writer | low | claude-haiku-3.X / gpt-4.1-nano | Documentation prose |

---

## Interrupt Policy

The orchestrator **must** pause and surface to the human under these conditions:

### 1. UNCERTAINTY
Any agent outputs `[UNCERTAINTY: ...]` in its response.
Action: Forward the uncertainty message verbatim, ask human for direction.

### 2. CONFLICT
Two agents produce conflicting recommendations on the same decision point within a workflow.
Example: Architect recommends approach A, MicroPython specialist flags memory risk with A.
Action: Present both positions, list options, ask human to decide.

### 3. SECURITY_RISK
Security agent flags any change as higher than LOW risk.
Risk levels: LOW (auto-proceed) | MEDIUM (notify, wait 300s) | HIGH (hard stop, require explicit human approval)
Action on HIGH: Full stop, do NOT commit or push until human approves.

### 4. TEST_FAILURE
Automated test suite (`pytest`) fails after two consecutive autonomous retry cycles (for the same failure).
First failure: Developer retries (only fix first failure reason) with updated approach.
Second failure: Interrupt. Present failure output, ask human.

### 5. COMMIT_GATE
Any of these git operations are about to execute:
- `git push` to a non-`wip/` branch
- `git push --force` (forbidden)
- `gh pr create` (draft PRs are OK to auto-create; `--ready` requires approval)
- `git tag`

Auto-approve: commits to `wip/` branches and `feat/`, `fix/` branches in progress.
Require approval: merges to `main` (forbidden), release tags, marking a draft PR as ready.

---

## Provider Configuration

The orchestrator reads whichever of these environment variables is present, in order of
preference. Set in `.env` (gitignored) or in the OpenClaw skill environment on the VPS.

```
# Anthropic
ANTHROPIC_API_KEY=...

# OpenAI
OPENAI_API_KEY=...

# GitHub Copilot (via proxy — see aider docs for copilot setup)
GITHUB_TOKEN=...

# Local / Ollama
OPENAI_BASE_URL=http://localhost:11434/v1
```

If multiple keys are present, the orchestrator selects based on the model tier table above.
High-tier roles always prefer the highest-capability available model.

---

## WIP Branch Convention

```
feat/<short-description>      — new feature
fix/<short-description>       — bug fix
refactor/<short-description>  — refactoring
wip/<YYYYMMDD-HHMM>          — autonomous VPS pipeline run
docs/<short-description>      — documentation only
```

Commits in each branch follow Conventional Commits format:
`type(scope): message`
Types: `feat`, `fix`, `test`, `docs`, `chore`, `refactor`, `style`, `perf`

---

## Security Auto-Trigger Rules

The orchestrator invokes the Security agent AUTOMATICALLY (without being asked) when
any workflow involves changes to these paths:

```
src/keystore/
src/rng.py
src/hosts/
bootloader/core/
bootloader/keys/
```

Severity thresholds:
- Touching key derivation, signing, or seed handling: HIGH (hard stop for human approval)
- Touching PIN logic, lockout, or session management: MEDIUM
- Touching interfaces, communication protocols: LOW
