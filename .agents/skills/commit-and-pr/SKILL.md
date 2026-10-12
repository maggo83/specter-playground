---
name: commit-and-pr
description: Split a working-tree diff into atomic commits and write commit messages and PR descriptions for this repo. Use when the user asks to commit, to break changes into logical commits, or to write or update a PR description.
argument-hint: "[<focus area>]"
---

# Commits and PR descriptions

The general prose rules (no em dashes, no filler words, no AI attribution) are in AGENTS.md under "Git, PRs and Writing". This skill adds the mechanics and the shape of the text.

Do not push and do not open a PR before the user has reviewed the changes.

## Splitting a diff into atomic commits

1. Look at everything: `git status`, `git diff`, `git diff --cached`, `git log --oneline -10`.
2. Group the changes. Each commit is one logical step that leaves the tests passing:
   - isolated bug fixes, independent of everything else
   - refactors and moves, separate from behavior changes
   - a feature's core, separate from its integration
   - tests, with the code they cover or right after it
   - docs, usually their own commit
   - submodule pointer bumps (`devtools/`, `f469-disco/`) and other generated or vendored files, each on their own
3. Stage deliberately: `git add <files>` for whole files, `git add -p` when one file holds two logical changes. Check `git diff --cached` before every commit.
4. If changes are intertwined and cannot be split, commit them together and say why in the body.
5. When a signature changes, grep for every caller before committing.
6. Before each commit, check the staged diff against the Core Invariants in AGENTS.md. If it touches entropy, secrets or anything shown for signing, say in the body how the invariant is upheld; if it touches none, nothing needs to be written.

## Commit message

Title: `type(scope): summary`

- type: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `build`
- scope: the component or directory touched (`mockui`, `devtools`, `device`, ...); omit it for repo-wide changes
- imperative, lowercase after the colon, no period, 72 characters or fewer

Body, after a blank line: one to three short paragraphs of prose, wrapped at 72.

- Say why: the problem, and for a fix the root cause. The diff already shows what.
- Add what helps review: algorithm or design choice, trade-offs, compatibility, a measured number.
- Do not restate the title. Do not list changed files. Do not use bullet summaries.
- Reference issues and specs (BIP numbers, links) where they matter.

Illustrative example:

```
fix(mockui): keep the scroll position after deleting a seed entry

Deleting an entry rebuilt the list from the top, so the user lost their
place in a long list. We now record the scroll offset before the
rebuild and restore it afterwards, clamped to the new list length.
```

## PR description

- Open with one or two paragraphs of prose: what the PR does and why, the problem it solves or the use case it enables.
- Then `##` sections only where they help (design, testing, open questions), still mostly prose. Code, output and screenshots are welcome when they show something concrete.
- State how it was tested, and what could not be tested here (for example on-device behavior).
- Link specs and related PRs inline on first mention.
- For a large PR, point readers at the individual commit messages for the step-by-step detail.
- Checkbox lists are fine to track remaining work in a draft PR, not as the main content.
- No "Key highlights", "Summary of changes" or similar headers.
