# Workflow: Release

## Purpose
Package completed work into a versioned release — changelog, build, firmware image,
and release PR targeting main.
THIS WORKFLOW IS STILL A DRAFT AND NEEDS TO BE REWORKED / REVIEWED BY A HUMAN BEFORE USE.

## When to Use
- Sprint is complete and a set of merged PRs is ready to ship
- A critical fix needs an out-of-band release
- Requested explicitly by the human

---

## Stages

### Stage 0 — Branch
**Agent**: Scrum Master
```
- git checkout main && git pull
- git checkout -b release/<version>   # e.g. release/v1.2.0
```

### Stage 1 — Collect Changes
**Agent**: Scrum Master
- List all commits/PRs since last release tag
  ```bash
  git log $(git describe --tags --abbrev=0)..HEAD --oneline
  ```
- Categorise by type: Added, Changed, Fixed, Security
- Pass list to Doc Writer

### Stage 2 — Release Notes
**Agent**: Doc Writer
- Promote `[Unreleased]` section in `CHANGELOG.md` to `[<version>] - YYYY-MM-DD`
- Add new empty `[Unreleased]` section at top
- Write human-readable summary (2-3 sentences) for the PR description
- If any Security entries: confirm Security agent reviewed them

**Commit**: `docs(release): prepare changelog for v<version>`

### Stage 3 — i18n Final Compile
**Agent**: i18n Specialist
- Run `nix develop -c make sync-i18n` — must report OK
- Run `nix develop -c make build-i18n ADD_LANG=de` — compile all lang bins
- Verify all `lang_XX.bin` files are up to date

**Commit**: `chore(i18n): compile lang bins for v<version>`

### Stage 4 — Build
**Agent**: Developer (or Orchestrator directly)
```bash
nix develop -c make unix                    # Rebuild simulator binary
nix develop -c make mockui ADD_LANG=de      # Build full STM32 firmware: bin/mockui.bin
nix develop -c make build-flash-image       # Build FAT12 FS image
```
All three must succeed without errors. If any fails:
`[UNCERTAINTY: build failed at make <target>]`

**Commit**: `chore(build): update build artifacts for v<version>`

### Stage 5 — Final Test Pass
**Agent**: Tester
- Run full `pytest` suite — must be 100% green
- Run simulator smoke test: `start_simulator`, navigate to MainMenu, `stop_simulator`
- If any failure: STOP — do not tag until fixed

### Stage 6 — Security Sign-off (conditional)
**Agent**: Security
- Triggered if any Security entries in CHANGELOG for this release
- Final sign-off that all security fixes are correctly documented and not accidentally
  reintroduced

### Stage 7 — Tag and PR
**Agent**: Scrum Master

> INTERRUPT: `[INTERRUPT: COMMIT_GATE]` — inform human before tagging

After human approval:
```bash
git tag -a v<version> -m "Release v<version>"
git push origin release/<version>
git push origin v<version>
gh pr create --title "release: v<version>" --body "<release summary>"
```

---

## Version Numbering
Follow semantic versioning (MAJOR.MINOR.PATCH):
- PATCH: bug fixes only
- MINOR: new features, backward compatible
- MAJOR: breaking changes (rare for device firmware)

## Completion Checklist
- [ ] `CHANGELOG.md` has versioned entry
- [ ] `nix develop -c make mockui ADD_LANG=de` produces `bin/mockui.bin` cleanly
- [ ] `make build-flash-image` succeeds
- [ ] `pytest` 100% green
- [ ] `nix develop -c make sync-i18n` reports OK
- [ ] Human approved tag creation
- [ ] Tag pushed to GitHub
- [ ] Release PR open
