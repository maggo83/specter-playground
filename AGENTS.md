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

# Core Invariants

A signing device exists to do three things. Every change, review and commit
checks that nothing introduced, and nothing already there, defeats one of them.
A change that touches none says so in one line. A change that weakens one is a
blocker and goes to the user first (see Decision Checkpoints).

1. **Entropy is random.** Entropy the device generates comes from a real random
   source and is never predictable, reused or derived from guessable input. If
   the source fails, the operation fails; there is no weaker fallback. Other
   entropy (dice, user input) may be mixed in, never at the cost of reducing it.
2. **Keys stay safe.** Seed, private keys and passphrase are never exposed
   beyond what the user explicitly asked for (for example showing the recovery
   phrase for a backup). Not in logs, error messages, host links, debug output
   or unencrypted storage, and not kept in memory longer than needed.
3. **What you see is what you sign.** What the user is shown for confirmation is
   factually correct, and the signature covers exactly the transaction they
   confirmed. The display may omit details the user chose not to see; it never
   shows something different from what is signed. Derive both from the same
   parsed data, and invalidate the confirmation if that data changes.

How to check them: [backend-security lens](.agents/skills/code-review/references/backend-security.md).

# Working Rules

## Managing Complexity

The game is managing complexity. Every change should fight accidental
complexity and spend its budget on what is essential.

- **Eliminate the failure mode before handling it.** Ask first whether the
  design can make a bad state unrepresentable: a type, an invariant, an
  ordering, a narrower API.
- **Simple design over defensive code.** Extra branches, flags, retries or
  special cases for a rare path are usually a design smell.
- **Weigh the machinery against the odds.** Say how likely and how bad the case
  is. For a rare, cheap failure a clear error or a documented assumption beats
  a mechanism.
- **In review, chase the claim, not the volume.** State each finding in one
  sentence, check that real inputs and callers can reach it, and dismiss
  unreachable cases with the reason instead of patching them.
- **Prefer the smaller diff** when two solutions have the same properties.

## Single Source of Truth

Every fact lives in exactly one place and everything else links to it. Copies
drift, and drift is hard to see. This file follows the rule: it links to the
devtools docs instead of repeating them.

- Before writing a fact into a doc, prompt or comment, search for where it
  already lives and link there.
- Refer to code by path and symbol, not by pasted snippets or line numbers.
  Generated artifacts (docs/MockUI screenshots, i18n tables) are regenerated,
  never edited by hand.
- Found a duplicate? Keep the copy closest to the code, replace the other with
  a link, and say so in the commit.
- A rule a test or lint can check belongs in the test or lint, not in prose.
- Tool-specific files hold no content of their own: `CLAUDE.md` imports this
  file, and `.claude/skills` and `.claude/agents` are symlinks into `.agents/`.

## Decision Checkpoints

Decide **who** to ask before deciding what to do.

- **Judgment call** (is this sound, what am I missing, which design): use the
  `advisor` skill, but only when the main session runs on a cheap tier. On a
  top-tier session reason it through yourself. About once per non-trivial task.
- **Preference or scope call** only the user can settle: stop and ask with
  concrete options. Always for: removing or skipping tests, deleting code or
  files (dead imports are fine), new patterns or dependencies, workarounds
  after the intended approach failed, adding or dropping requested scope,
  public interface changes, cryptographic or fund-relevant code, and any action
  on a board (see Hardware Safety above).

## Cost and Parallelism

Spend the expensive model on judgment and the cheap one on volume. Tiers:
**cheap** (mechanical, well-specified work), **standard** (the default session),
**top** (planning, hard decisions, final review). Map them to concrete models in
your tool's settings; nothing in the repository names a model.

| Need | Use | Tier |
|------|-----|------|
| Quick answer about how code works | `quick-dive` skill, `code-scout` agent | cheap |
| Full architecture picture with diagrams | `deep-dive` skill, `architecture-archaeologist` agent | standard or top plans, cheap tracks |
| N independent items (files, audits) | `orchestrate` skill | top plans, cheap executes |
| Stuck, or at a fork | `advisor` skill | top |
| Review of an ordinary diff or PR | `code-review` skill | by lens |
| Finished, before telling the user | `adversarial-review` skill | top |

- Sub-agents share no context or prompt cache. Give them a relevant packet (the
  question, the evidence, the constraints), not the whole transcript.
- Fan out only scoped, independent work. Sequential or single-file work is just
  done.
- Scratch reports go in `history/` (gitignored). Never commit plans, drafts,
  status or review reports.

## Finishing Work

A task is complete only when every acceptance criterion is met, `make test`
passes, the Core Invariants still hold and it works end to end. Say explicitly
what could not be run here (on-device tests, board-only behavior); never mark
something done by omission.

Before calling a substantive change done or opening a PR, run
`adversarial-review` once. Verify each finding against the code before acting.
One pass is the rule; a review that keeps surfacing rare, unreachable scenarios
is the complexity anti-pattern above, not a reason to keep going.

## Git, PRs and Writing

- Commits and PR descriptions: see the `commit-and-pr` skill. Atomic commits,
  title `type(scope): summary`, body explains why. Check the diff against the
  Core Invariants before every commit.
- No AI attribution in commits or PRs, and no AI tool names in branch names.
- Do not push or open a PR before the user has reviewed the changes.
- Prose in commits, PRs, docs and chat: state things plainly, no metaphor for
  show, prose over bullets unless the content is a list. No em dashes. No filler
  transitions ("Additionally", "It's worth noting"). Avoid "comprehensive",
  "robust", "streamlined", "leverage", "utilize", "facilitate". No self-praise,
  no sign-offs, no emojis.

## Codifying Corrections

When the user corrects a behavior that could recur, or you catch yourself going
off the rails, suggest the `codify` skill in one line (do not run it unasked).
It puts the rule in the narrowest place that removes the failure mode and
tightens an existing rule before adding one, so this file stays short.

## Skills and Agents

Canonical files: `.agents/skills/<name>/SKILL.md` (open Agent Skills layout) and
`.agents/agents/<name>.md`. Edit only there. `ls .agents/skills .agents/agents`
lists them; each file's description says when to use it.
