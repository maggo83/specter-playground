# Workflow: Bug Fix

## Purpose
Fast, focused fix for a confirmed bug — from reproduction to merged PR.

## When to Use
- Confirmed wrong behaviour (not a feature request)
- Test failure that needs fixing
- Regression from a recent change

---

## Stages

### Stage 0 — Branch
**Agent**: Scrum Master
```
- git checkout main && git pull
- git checkout -b fix/<short-description>
```

### Stage 1 — Reproduce
**Agent**: Tester
- Understand the bug report: what is expected, what actually happens
- Write a failing test that reproduces the bug
- Use MCP simulator tools for UI bugs: `start_simulator`, `set_state`, `click_widget`
- Use pytest for logic bugs: mock the LVGL layer, isolate the faulty component
- Run the test — confirm it fails with the described symptom

**Commit**: `test(<scope>): add failing regression test for <bug>`

### Stage 2 — Diagnose
**Agent**: Developer
- Read the failing test
- Identify root cause — use `code-rag` MCP tool to search for related code if needed
- Consult `micropython-specialist` if the bug is runtime/memory related
- Consult `lvgl-mockui-specialist` if the bug is UI/widget related
- Document root cause in 2-3 sentences (included in commit message body)

### Stage 3 — Fix
**Agent**: Developer
- Implement the fix — minimal change to fix the specific bug
- Avoid refactoring unrelated code in the same PR
- Run the reproduction test — must now PASS
- Run full `pytest` suite — no regressions

> If full suite has unexpected failures: emit `[UNCERTAINTY: regression in unrelated tests]`

**Commit**: `fix(<scope>): <description>\n\nRoot cause: <2-3 sentences>`

### Stage 4 — Security Check (conditional)
**Agent**: Security (auto-triggered)
- Triggered if fix touches `src/keystore/`, `src/rng.py`, `bootloader/`, `src/hosts/`
- Quick focused review: does the fix introduce any new risk?

### Stage 5 — Documentation
**Agent**: Doc Writer
- Add entry to `CHANGELOG.md` under `[Unreleased] → Fixed`
- Update screen docs only if the bug was visual and the fix changes appearance

**Commit**: `docs: update changelog for fix/<description>`

### Stage 6 — PR
**Agent**: Scrum Master
- Verify: failing test now passes, full pytest suite green, no uncommitted changes
- Open draft PR: `gh pr create --draft --title "fix: <description>" --body "..."`

> INTERRUPT: `[INTERRUPT: COMMIT_GATE]` — inform human, share PR URL

---

## Completion Checklist
- [ ] Reproduction test written and now passing
- [ ] Full `pytest` suite green (no regressions)
- [ ] Root cause documented in commit message
- [ ] `CHANGELOG.md` updated
- [ ] Draft PR open
