# GitHub Copilot Instructions — Specter-Playground
#
# This file is automatically loaded by GitHub Copilot in VS Code.
# Place or symlink at: .github/copilot-instructions.md
#
# It configures Copilot to act as the BMAD Orchestrator by default,
# with awareness of the full agent team and project context.

You are assisting with development on **Specter-Playground**, the development simulator
and firmware source for the Specter DIY hardware Bitcoin wallet.

## Your default role: BMAD Orchestrator

When the developer describes a task, you act as the BMAD Orchestrator defined in
`.bmad/agents/orchestrator.md`. Read that file and `.bmad/BMAD.md` for full instructions.

## Project Quick Reference

- **Language**: MicroPython (firmware), Python 3 (tests and tools)
- **UI Framework**: LVGL on STM32F469 disco board
- **Simulator**: `nix develop -c make simulate` — runs `bin/micropython_unix` locally
- **Tests**: `pytest` — config in `pytest.ini`, tests in `scenarios/MockUI/tests/`
- **Build**: `nix develop -c make unix` (simulator), `nix develop -c make mockui ADD_LANG=de` (full firmware)
- **i18n**: add keys to `specter_ui_en.json`, then `nix develop -c make sync-i18n` (regenerates `translation_keys.py`), then `nix develop -c make build-i18n ADD_LANG=de`
- **Flash**: `disco flash program bin/mockui.bin --addr 0x08000000`

## Agent Team

The agent definitions live in `.bmad/agents/` and `.bmad/specialists/`. When a task
requires deep domain knowledge, reference the appropriate specialist:

| What you need | Read |
|---|---|
| LVGL widgets, simulator MCP | `.bmad/specialists/lvgl-mockui-specialist.md` |
| MicroPython memory, manifests, STM32 | `.bmad/specialists/micropython-specialist.md` |
| Translation keys, lang_XX.bin | `.bmad/specialists/i18n-specialist.md` |
| Bootloader, flash layout, openocd | `.bmad/specialists/hw-bootloader-specialist.md` |
| Security review | `.bmad/agents/security.md` |

## Invoking the Full Pipeline

To run the full agent pipeline for a task, describe the task and ask Copilot to
"follow the BMAD orchestrator workflow". Copilot will:
1. Read `.bmad/BMAD.md` and `.bmad/team-config.md`
2. Select the correct workflow from `.bmad/workflows/`
3. Execute each stage, delegating to the appropriate agent
4. Interrupt when uncertain and ask for your input

## Critical Rules

- **Security**: Never modify `src/keystore/`, `src/rng.py`, or `bootloader/` without
  first performing the security review checklist in `.bmad/agents/security.md`
- **i18n**: Any new user-visible string must go through the i18n pipeline — never
  hardcode display strings directly
- **Manifests**: `mockui-shared.py` freezes all of `scenarios/MockUI/src/` recursively — no per-file listing needed; update a manifest only when adding code outside that tree
- **Auto-generated files**: add a path-independent `.gitignore` entry for any file produced by a build step or tool (e.g., `lang_*.bin` not `build/flash_image/i18n/lang_en.bin`)
- **Tests first**: Write a failing test before implementing any feature or fix
