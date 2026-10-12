# Project Context

## Codebase Overview

| Directory | Description |
|-----------|-------------|
| `scenarios/` | **New MockUI** - clickable prototype, no real functionality yet |
| `specter-diy-src/` | **Old specter-diy** (symlink) - working code, ugly UI, reference implementation |
| `f469-disco/` | MicroPython + LVGL build system, C modules. Temporarily pinned to `maggo83/f469-disco_disco_tool` branch `fix/sdl-screenshot-rgba32` (SDL screenshot + color fix) until [miketlk/f469-disco#1](https://github.com/miketlk/f469-disco/pull/1) and its follow-up [#3](https://github.com/miketlk/f469-disco/pull/3) are merged |
| `devtools/` | [specter-devtools](https://github.com/maggo83/specter-devtools) submodule: shared simulator/hardware control, F469 `disco` tool, simulator control runtime |

## Simulator and Hardware Control

To test, verify or prototype behavior and UI, use specter-devtools instead of
reasoning from the code. Try in this order: unit tests (`make test`), then the
simulator, and a board only with the user's approval. A screenshot from the
simulator is stronger evidence than a code reading.

**Board approval is asked once per session**, with one warning and one yes or
no, not per test and not per operation. Ask at the first point where a board
would help. If none is detected, ask anyway: never conclude that no board is
available just because none is visible, the user can usually attach one. The
question names, in plain words, everything the agent may then do, taken from
[Hardware Safety](devtools/AGENTS.md#hardware-safety) (flashing, erasing, lock
and unlock, power, resets, `explore` tapping buttons and changing device state),
and says the board must hold no real funds. After a yes, use the board for all
of that for the rest of the session without asking again.

**Clean checkout:** devtools is a submodule, so `devtools/` is empty until
`git submodule update --init --recursive` has run, and the `specter-devtools`
command does not exist until devtools is set up. When either is missing, do both
yourself, no approval needed: init the submodules, then follow the setup in the
[devtools README](devtools/README.md) and run the command as
`devtools/.venv/bin/specter-devtools`.

[specter-devtools](devtools/README.md), the `devtools/` submodule, controls the
simulator and an attached F469 board. Its own docs are the reference; read them
before using it:

- [devtools/README.md](devtools/README.md): setup (run it inside `devtools/`)
  and commands.
- [devtools/docs/control-contract.md](devtools/docs/control-contract.md):
  requests, responses, target differences, and
  [Visual Validation](devtools/docs/control-contract.md#visual-validation).
- [Tests and Verification](devtools/AGENTS.md#tests-and-verification): what each
  check proves, and how to say what you verified when reporting.
- [Hardware Safety](devtools/AGENTS.md#hardware-safety): what to ask the user
  before acting on a board.

What this repository adds:

- `make simulate-automation` builds the Unix simulator and starts MockUI with
  its control server (`--control`, TCP port 9876). The simulator freezes
  `devtools/simulator/sim_control` (listed in `manifests/unix.py`), so rebuild
  after checking out another devtools commit. To restart it, stop it and run the
  target again; *EADDRINUSE* means a stale process still holds the port
  (`lsof -ti:9876 | xargs kill`).
- MockUI starts from the preset `/flash/presets/mockui.json` if there is one:
  `make simulate*` uses `dev`, other targets only with `MOCKUI_PRESET=<name>`
  (see [README](README.md#mockui)).
- `specter-devtools --target simulator explore docs/MockUI/screens` refreshes
  the screenshots in [docs/MockUI](docs/MockUI/index.md).
- The hardware tests in `scenarios/MockUI/tests_device/` use
  `devtools/f469/disco`.

## RAG Code Search

Optional semantic search over both repos, exposed as the MCP tool
`search_codebase` for agents that have the `code-rag` MCP server configured
(see `docs/rag-setup.md`).

```bash
# Re-index after code changes
make rag-index
```

## Key Points

- MockUI in `scenarios/` is the **target design** - modern, clean
- Old code in `specter-diy-src/` has **working logic** to reference
- Goal: port functionality from old to new UI
