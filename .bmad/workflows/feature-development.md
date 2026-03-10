# Workflow: Feature Development

## Purpose
Full lifecycle for new features — from vague idea to merged PR.
Use this workflow for any task classified as `feat` by the PM.

## When to Use
- New screen or menu
- New device capability exposed in UI
- New wallet management flow
- New settings option
- Any user-visible addition

---

## Stages

### Stage 0 — Branch
**Agent**: Scrum Master
```
- git checkout main && git pull
- git checkout -b feat/<short-description>
```

### Stage 1 — Brief
**Agent**: PM
- Read the raw task description (from user, issue, or message)
- Produce a Task Brief with acceptance criteria
- Flag security sensitivity and which specialists are needed
- Output: `Task Brief` document
- Iterate with Human until human confirms Task Brief is clear and actionable

**Commit**: `docs(design): add task brief for <feature>`

### Stage 2 — Design
**Agent**: Architect
- Read Task Brief
- Consult `micropython-specialist` for memory/manifest questions
- Consult `lvgl-mockui-specialist` for widget architecture questions
- Produce Design Note
- Output: `Design Note` document

**Parallel**: UX Designer starts Stage 3 while Architect finalises

### Stage 3 — Screen Spec
**Agent**: UX Designer
- Read Task Brief + Design Note
- Consult `lvgl-mockui-specialist` for widget constraints
- Use MCP `get_widget_tree` on related existing screens for reference
- Produce Screen Spec with widget list, layout, navigation, new i18n keys
- Output: `Screen Spec` document

**Commit**: `docs(design): add screen spec for <feature>`

### Stage 4 — Tests (failing)
**Agent**: Tester  [parallel with Stage 4b]
- Read Task Brief acceptance criteria + Screen Spec
- Write pytest unit tests (they will fail — implementation not done yet)
- Write MCP simulator tests (interact via MCP tools; stub with `pytest.mark.skip` if simulator not running)
- Write device tests (flash + interact on real hardware; stub with `pytest.mark.skip` until Stage 6)
- Run `pytest` — confirm tests exist and fail as expected
- Output: test files in `scenarios/MockUI/tests/test_<feature>.py`

**Commit**: `test(<scope>): add failing tests for <feature>`

### Stage 4b — i18n Keys
**Agent**: i18n Specialist  [parallel with Stage 4]
- Read Screen Spec for new translation keys
- Add English strings to `scenarios/MockUI/src/MockUI/i18n/languages/specter_ui_en.json`
- Run `nix develop -c make sync-i18n` — propagates keys to other language files, regenerates `translation_keys.py`
- Output: updated `specter_ui_XX.json` files, regenerated `translation_keys.py`

**Commit**: `chore(i18n): add translation keys for <feature>`

### Stage 5 — Implementation
**Agent**: Developer
- Read Design Note + Screen Spec + failing tests
- Consult `micropython-specialist` as needed
- Consult `lvgl-mockui-specialist` for LVGL API questions
- Implement feature: new/modified Python files in `scenarios/MockUI/src/MockUI/`
- Update `manifests/` only if new code is added *outside* `scenarios/MockUI/src/` (that tree is already fully frozen)
- Run `nix develop -c make simulate` — simulator must start without errors
- Run `pytest` — all tests must pass
- Run `nix develop -c make build-i18n ADD_LANG=de` — verify translations compile without errors (`lang_XX.bin` is gitignored, no commit needed)

> If tests still fail after two attempts: emit `[UNCERTAINTY: test failure after 2 attempts]`

**Commit**: `feat(<scope>): implement <feature>`

### Stage 6 — Device Validation
**Agent**: Tester
- Build full firmware: `nix develop -c make mockui ADD_LANG=de`
- Flash to hardware: `disco flash program bin/mockui.bin --addr 0x08000000`
- Remove `pytest.mark.skip` from device tests; run them on real hardware
- For each failing test, follow this triage order:
  1. **Assume test error first**: device tests interact with real hardware timing, serial ports, and state machines — prefer fixing the test before touching the implementation.
  2. Check for test-side issues: wrong timing/delays, incorrect state setup, hardware-specific quirks, test isolation problems
  3. Only after ruling out test issues: investigate whether the implementation is at fault
  4. If confirmed implementation bug: go back to Stage 5, fix, rebuild, reflash, retest
- After each fix cycle, re-run the full device test suite (not just the previously failing test)
- All device tests must pass before proceeding

> Device tests are NOT optional — a green simulator alone is not sufficient for PR.
> Emit `[UNCERTAINTY: device test failure after 3 fix cycles]` if still failing after three attempts — do not proceed to PR.

**Commit**: `test(<scope>): enable and pass device tests for <feature>`

### Stage 7 — Security Review (conditional)
**Agent**: Security
- Triggered ONLY if Task Brief flagged security sensitivity, OR if implementation
  touched `src/keystore/`, `src/rng.py`, `src/hosts/`, or `bootloader/`
- Perform security review checklist
- Output: Security Review with risk level

> HIGH risk: INTERRUPT → human must approve before continuing

### Stage 8 — Documentation
**Agent**: Doc Writer
- Update `docs/MockUI/screens/` for any modified or new screens
- Update `CHANGELOG.md` under `[Unreleased] → Added`
- Update affected `README.md` files if the feature touches a complex area (e.g., i18n, manifests)
- Run `nix develop -c make sync-i18n` one final time to confirm no drift

**Commit**: `docs(<scope>): update screen docs and changelog for <feature>`

### Stage 9 — PR
**Agent**: Scrum Master
- Verify: `pytest` passes (unit + simulator + device tests all green), `nix develop -c make simulate` starts, no uncommitted changes
- Open draft PR: `gh pr create --draft --title "feat: <description>" --body "..."`
- Fill PR description template (see `agents/scrum-master.md`)

> INTERRUPT: `[INTERRUPT: COMMIT_GATE]` — inform human PR is open, share URL

---

## Completion Checklist
- [ ] All acceptance criteria from Task Brief have a passing test
- [ ] `pytest` green (unit + MCP simulator tests)
- [ ] Device tests pass on real hardware
- [ ] `nix develop -c make simulate` starts without errors
- [ ] `nix develop -c make sync-i18n` reports OK
- [ ] `docs/MockUI/` updated
- [ ] `CHANGELOG.md` updated
- [ ] Draft PR open on GitHub
- [ ] Security review done (if triggered)
