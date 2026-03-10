# Workflow: Refactoring

## Purpose
Improve internal code quality without changing user-visible behaviour.

## When to Use
- Splitting a large module into smaller, more focused ones
- Extracting shared logic into a helper
- Improving naming, readability, or test coverage
- Reducing MicroPython heap usage
- Updating a manifest, build target, or tool script

## Key Constraint
Refactoring must not change observable UI behaviour. The test suite passing
before and after is the definition of success.

---

## Stages

### Stage 0 — Branch
**Agent**: Scrum Master
```
- git checkout main && git pull
- git checkout -b refactor/<short-description>
```

### Stage 1 — Scope
**Agent**: Architect
- Define exactly which files/components are being refactored
- Define the "before and after": what changes structurally, what stays the same
- Consult `micropython-specialist` if the goal is memory reduction (need before/after estimate)
- Confirm: is any user-visible behaviour changing? If yes → switch to feature-development workflow
- Output: Refactoring Scope document

**Commit**: `docs(design): add scope note for refactor/<description>`

### Stage 2 — Baseline Tests
**Agent**: Tester
- Run `pytest` and record current pass/fail state (baseline)
- Identify any gaps: are there areas being refactored with no test coverage?
- If gaps exist: write the missing tests BEFORE the refactoring starts

**Commit** (if new tests added): `test(<scope>): add coverage before refactor`

### Stage 3 — Refactor
**Agent**: Developer
- Execute refactoring as scoped by Architect
- Consult `micropython-specialist` for manifest changes or memory implications
- Run `pytest` after each logical sub-step — catch regressions immediately
- Run `nix develop -c make simulate` at the end — simulator must start cleanly

> If a refactor step causes unexpected test failure: emit `[UNCERTAINTY: refactor caused regression in <test>]`

**Commit** (per logical step): `refactor(<scope>): <what changed and why>`

### Stage 4 — Memory Verification (conditional)
**Agent**: MicroPython Specialist
- Triggered if the goal of the refactoring was memory reduction
- Run `micropython.mem_info()` in simulator before and after
- Report: bytes saved, any remaining opportunities

### Stage 5 — Documentation
**Agent**: Doc Writer
- Update `CHANGELOG.md` under `[Unreleased] → Changed`
- Update any code-level docs in `docs/` if module boundaries changed

**Commit**: `docs: update changelog for refactor/<description>`

### Stage 6 — PR
**Agent**: Scrum Master
- Verify: same tests pass as baseline, `nix develop -c make simulate` clean, no uncommitted changes
- Open draft PR

> INTERRUPT: `[INTERRUPT: COMMIT_GATE]` — inform human, share PR URL

---

## Completion Checklist
- [ ] All tests passing before and after (no behaviour change)
- [ ] `nix develop -c make simulate` clean
- [ ] Memory verified (if memory-reduction goal)
- [ ] Manifests updated (only if files moved outside `scenarios/MockUI/src/`)
- [ ] `CHANGELOG.md` updated
- [ ] Draft PR open
