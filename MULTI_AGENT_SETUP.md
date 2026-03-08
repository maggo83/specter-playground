# Multi-Agent Development Workflow — Specter-Playground

> Setup record created: 2026-03-08
> Purpose: Reference for reconstructing or understanding the multi-agent AI development
> workflow configured for this project.

---

## Overview

The project uses [BMAD Method v6](https://github.com/bmad-code-org/BMAD-METHOD) as the
agent framework backbone. Agent definitions live in `.bmad/` as provider-agnostic markdown
files. Thin adapters wire them to individual IDEs (VS Code + Continue.dev, GitHub Copilot,
Cursor, Claude Code). No single AI provider or IDE subscription is required.

A second phase (documented below) adds an always-on OpenClaw instance on a VPS, enabling
messenger-driven (Telegram/Signal) autonomous pipeline execution when away from the desk.

---

## Architecture

```
Developer (IDE / Telegram)
        │
        ▼
 Orchestrator Agent     ← reads .bmad/BMAD.md + team-config.md
        │
        ├──▶ PM Agent
        ├──▶ Architect Agent  ──▶ MicroPython Specialist (on-demand)
        ├──▶ UX Designer      ──▶ LVGL/MockUI Specialist (on-demand)
        ├──▶ Developer        ──▶ MicroPython Specialist (on-demand)
        ├──▶ Tester           ──▶ LVGL/MockUI Specialist (on-demand)
        ├──▶ Security Agent   ← auto-triggered on keystore/bootloader/rng changes
        ├──▶ Doc Writer       ──▶ i18n Specialist (on-demand)
        ├──▶ Scrum Master
        ├──▶ i18n Specialist
        └──▶ HW/Bootloader Specialist (on-demand)
```

**MCP Tools available to agents:**
- `lvgl-sim`: start/stop simulator, click widgets, get widget tree, screenshot
- `code-rag`: semantic search over MockUI and specter-diy source

---

## Phase 1 — Local Agent Team

### What was installed

- **BMAD v6 BMM module** — core framework, 34+ workflows
- **BMAD v6 TEA module** — Test Architect, risk-based test strategy
- Both installed via `npx bmad-method install`

### Directory layout

```
.bmad/
  BMAD.md                        — orchestrator entry point + conventions
  team-config.md                 — model assignments, interrupt policy
  agents/
    orchestrator.md
    pm.md
    architect.md
    ux-designer.md
    developer.md
    tester.md
    security.md
    doc-writer.md
    scrum-master.md
  specialists/
    micropython-specialist.md    — MicroPython + STM32F469 domain knowledge
    lvgl-mockui-specialist.md    — LVGL widget tree, simulator MCP, MockUI architecture
    i18n-specialist.md           — lang_XX.bin pipeline, sync-i18n, translation_keys.py
    hw-bootloader-specialist.md  — bootloader spec, flash layout, openocd, secure boot
  workflows/
    feature-development.md
    bug-fix.md
    refactoring.md
    release.md
  adapters/
    continue-dev.yaml            — Continue.dev profile definitions
    copilot-instructions.md      — loaded by VS Code GitHub Copilot
    cursor-rules.md              — loaded by Cursor

CLAUDE.md                        — repo root, auto-loaded by Claude Code
```

### How agents are invoked (per IDE)

| IDE / Tool | How to invoke the orchestrator |
|---|---|
| Claude Code CLI | `/orchestrate "task description"` or just describe the task naturally |
| Continue.dev | Switch to "Orchestrator" profile, describe task |
| Cursor | `@orchestrator task description` |
| VS Code + Copilot | Type task in Copilot chat with orchestrator instructions auto-loaded |

### Model assignments

Defined in `.bmad/team-config.md`. Each agent role maps to a model tier:

| Role | Tier | Rationale |
|---|---|---|
| orchestrator, architect, security | Opus / GPT-4.1 | Complex reasoning, ambiguity resolution |
| pm, ux-designer, scrum-master | Sonnet / GPT-4.1-mini | Structured output |
| developer, specialists | Sonnet / Codex | Code generation |
| tester, i18n-specialist, doc-writer | Haiku / small model | High-volume, low cost |

### Interrupt policy

The orchestrator pauses and notifies the human when:
- Any agent outputs `[UNCERTAINTY: ...]`
- Two agents produce conflicting recommendations
- Security agent flags risk above threshold
- Test suite fails after two autonomous retry cycles
- A `git push`, `git commit`, or PR action is about to execute (configurable)

### How to update agents

1. Edit the relevant `.bmad/agents/*.md` or `.bmad/specialists/*.md` file
2. Commit to the repo — all team members pick up the change on next pull
3. No deployment or restart required; agents read definitions at invocation time

### Key project-specific knowledge encoded in agents

- `micropython-specialist`: `const()` optimisation, `manifests/*.py` frozen modules,
  `bin/micropython_unix` vs. hardware differences, `make unix` / `make disco` targets,
  STM32F469 disco board peripherals
- `lvgl-mockui-specialist`: LVGL widget hierarchy, `NavigationController`,
  `SpecterState`/`UIState`, MCP simulator tools, TCP control protocol
- `i18n-specialist`: `lang_XX.bin` binary format, `lang_compiler.py`,
  `tools/sync_i18n.py`, `translation_keys.py`, `make build-i18n`
- `hw-bootloader-specialist`: bootloader spec (`bootloader/doc/bootloader-spec.md`),
  flash memory map (`bl_memmap.h`), `openocd.cfg`, `make build-flash-image`
- `security`: hardware wallet threat model, key material lifecycle, PIN brute-force
  protection, secure boot chain; auto-invoked on changes to `src/keystore/`,
  `bootloader/core/`, `src/rng.py`

### MCP server fixes applied

- `.mcp.json`: replaced hardcoded `/Users/kim/...` paths with `$PROJECT_ROOT`-relative
  paths using a wrapper script
- `mcp-servers/lvgl-sim/mcp_server.py`: replaced macOS `screencapture` with
  Pillow-based RGB565 raw file reader (`/tmp/sim_screenshot.raw`) — works on Linux

---

## Phase 2 — VPS + Messenger Gateway

> Status: Not yet implemented. Reference for future setup.

### Hardware

- Generic Server — AMD EPYC, 4vCPU, 8GB RAM, 128GB SSD, Ubuntu 24.04 LTS

### Components

| Component | Purpose |
|---|---|
| [OpenClaw](https://openclaw.ai) | Always-on personal AI assistant + messenger gateway |
| `aider` | Headless coding agent that runs BMAD pipeline against the repo |
| Telegram bot | Messenger channel (Signal as alternative) |
| OpenAI or Anthropic API key | Pay-per-token LLM for VPS pipeline (separate from Copilot) |
| VS Code Remote SSH | IDE access to VPS for debugging without GUI |

### Architecture

```
Phone (Telegram) → OpenClaw (VPS) → aider CLI → .bmad/ orchestrator → git push → GitHub PR
                        ↑                                                              │
                        └─── "PR #N ready" / "[UNCERTAINTY: ...]" notification ───────┘
```

### Setup steps (when ready to implement)

1. `curl -fsSL https://openclaw.ai/install.sh | bash` on VPS
2. Configure Telegram bot token in OpenClaw
3. Configure OpenAI/Anthropic API key (pay-per-token)
4. `pip install aider-chat`
5. `git clone` the repo to VPS with SSH deploy key
6. Install `gh` CLI and authenticate for PR creation
7. Write `specter-dev` OpenClaw skill (see below)

### The `specter-dev` skill (pseudocode)

```bash
# ~/.clawd/skills/specter-dev/run.sh
# Called by OpenClaw with $TASK set to the Telegram message content

git -C ~/specter-playground pull
git -C ~/specter-playground checkout -b wip/$(date +%Y%m%d-%H%M)

notify "Starting pipeline for: $TASK"

aider \
  --message "Read .bmad/BMAD.md and follow the orchestrator. Task: $TASK" \
  --auto-commits \
  ~/specter-playground

# aider reports back via stdout — parse for [UNCERTAINTY], test failures, etc.
# Push branch and open draft PR
git -C ~/specter-playground push origin HEAD
gh pr create --draft --title "wip: $TASK" --body "Automated pipeline run"

notify "PR opened: $(gh pr view --json url -q .url)"
```

### Debugging on VPS

- **GitHub browser**: branch is always pushed, state is always inspectable
- **Pull to laptop**: `git fetch && git checkout wip/YYYYMMDD-HHMM`
- **VS Code Remote SSH**: `code --remote ssh-remote+YOUR_VPS ~/specter-playground`
  — full IDE experience (file explorer, git panel, Copilot, terminal) over SSH

### WIP branch convention

- Pipeline always works on a named `wip/YYYYMMDD-HHMM` branch
- Commits frequently with conventional commit messages at each workflow stage
- Never force-pushes
- Draft PR opened immediately so state is visible before pipeline completes

---

## Key decisions and rationale

| Decision | Rationale |
|---|---|
| `.bmad/` as canonical location (not `.claude/commands/`) | Provider-agnostic; works with any IDE via thin adapters |
| BMAD v6 over custom framework | Hours to set up, community-maintained, 34+ workflow templates, TEA module for test-first |
| BMAD v6 over code-based frameworks (LangGraph, CrewAI) | IDE-native, zero infrastructure for Phase 1, agent definitions editable as markdown by anyone |
| `aider` over Claude Code CLI on VPS | Any LLM API key, no Anthropic subscription required, open-source |
| OpenAI/Anthropic pay-per-token for VPS pipeline | Clean separation from Copilot subscription; pipeline costs are single-digit $/month |
| Telegram over Signal for messenger | Official bot API, first-class OpenClaw support, no fragile CLI tools |
| Frequent WIP commits over large uncommitted diffs | Pipeline state always inspectable from GitHub or any machine |
| STM32 knowledge in `micropython-specialist` | Useful coupling is runtime vs. hardware, not chip datasheet in isolation |
| Security as standard agent, not specialist | Auto-invoked on any crypto/keystore change — too critical to be opt-in |

---

## References

- [BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD) — framework source
- [BMAD Docs](https://docs.bmad-method.org/) — tutorials and reference
- [OpenClaw](https://openclaw.ai) — VPS gateway
- [aider](https://aider.chat) — headless coding agent
- [docs/lvgl-sim-mcp.md](docs/lvgl-sim-mcp.md) — simulator MCP documentation
- [docs/rag-setup.md](docs/rag-setup.md) — RAG code search setup
