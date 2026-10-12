---
name: code-review
description: Review a diff, branch or PR with specialist reviewers chosen by what changed (language lens, backend and crypto lens, UX lens, tests, docs), then triage into one ranked report. Report-only. Use for ordinary reviews and pre-PR checks; for the closing gate on your own finished work use adversarial-review.
argument-hint: "[<commit-range> | <branch> | <PR number>] [--focus=security|ux|tests]"
---

# Code Review

Report-only. Findings go to the chat, not into a file in the repo.

## 1. Scope

Resolve one diff command and use it for every reviewer, so they all see the same surface:

```bash
base=$(git merge-base origin/main HEAD)
git diff "$base"..HEAD --stat
```

A range, branch or PR number from the arguments replaces the default. With no commits ahead of the base, review the working tree (`git diff HEAD`).

## 2. Baseline

Run `make test` and note what is already red, so existing breakage is not blamed on the change. Continue the review if it fails or times out and say so in the report. Things that need the board (`scenarios/MockUI/tests_device/`) are listed as not run.

## 3. Pick the lenses from the changed paths

| Changed paths | Lens | Reviewer |
|---|---|---|
| every diff | the three Core Invariants in AGENTS.md, answered per invariant as "not touched" or "upheld because ..." or "violated" | every reviewer |
| `*.py` | [references/python.md](references/python.md) | `code-reviewer` |
| `*.c`, `*.h` (`bootloader/`, `f469-disco/usermods/`) | [references/c.md](references/c.md) | `code-reviewer` |
| `src/keystore/`, `src/hosts/`, `src/apps/`, `src/rng.py`, `bootloader/`, seed, PSBT, signing, anything touching keys or funds | [references/backend-security.md](references/backend-security.md) | `security-auditor` |
| `scenarios/MockUI/`, `src/gui/`, themes, i18n, `docs/MockUI/` | [references/ux.md](references/ux.md) | `code-reviewer`, plus `design-iterator` if visual evidence is needed |
| tests added, changed, or missing for new logic | the testing section of the language lens | `test-engineer` |
| docs changed | claims versus code | `documentation-double-checker` |

Skip a lens whose paths did not change, except the first row, which always applies. `--focus` narrows the rest.

## 4. Dispatch

Launch the selected reviewers together in one message. Give each: the diff command, a short brief (what the change does and why), the lens file path, and this skeleton:

> You are an adversarial reviewer. Try to break this change, do not grade it. Report only findings you can argue concretely from the code. For each: `path:line` or symbol, severity, the concrete trigger scenario (inputs and state, wrong outcome), a minimal fix sketch. A verified "not a bug" is useful. No pleasantries.

Cheap tier is enough for the language lens on a small diff; use the standard or top tier for the security lens and for key-handling code.

## 5. Triage

Merge duplicates. Verify each finding against the code and drop what cannot be reached from real inputs and callers, with the reason (see Managing Complexity in AGENTS.md). Rank the rest.

## 6. Report

- **Blocker**: a violated Core Invariant (random entropy, keys safe, what you see is what you sign), wrong result on a fund-relevant path, secret exposure, corrupted persistent state, security issue, broken interface without migration.
- **Critical**: likely bug, missing test for non-trivial logic, resource leak, incomplete error handling.
- **Smell**: poor abstraction, duplication (including duplicated facts, see Single Source of Truth), missing docs.

Give a verdict (approve, approve with conditions, changes required) in one line, then findings by severity, each with location, scenario and fix. Add what was not run and why. Be direct and specific; do not pad with praise.
