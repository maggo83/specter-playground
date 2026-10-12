---
name: adversarial-review
description: Closing gate on a substantive or risky change before calling it done or opening a PR. One top-tier sub-agent does a single report-only pass over three axes (verify the load-bearing invariants, especially what you could not run locally; find simplifications; hunt for live variants of the bug shape just fixed). You then verify each finding and act. Skip for trivial or fully test-covered changes.
argument-hint: "[<branch | commit range | the change you just made>] [--tier=top|standard]"
---

# Adversarial Review

A fresh reader without the mental model that wrote the code breaks author bias. That holds on any tier, so run it even when the session is already top tier. You stay the author: the reviewer reports, you verify and decide.

## When

- A substantive or risky change is finished and you are about to say so.
- Part of it cannot be validated here: on-device tests, board-only behavior, rendering on the real display, anything under `scenarios/MockUI/tests_device/`.
- A reviewer found a real bug and you want to know if the same shape lives elsewhere.
- Before a PR on key handling, signing, seed storage or other fund-relevant code.

Not for a trivial change. For an ordinary diff review use `code-review`.

## Mechanics

One sub-agent, top tier, report-only. One strong reviewer with a tight prompt beats a fan-out here: you want a coherent trace, not a vote.

1. **Commit first.** The reviewer reads the diff from git, so uncommitted work is invisible to it. Commit under review (fixups are fine) or tell it to include the working tree and untracked files. Commit only if the user wants commits.
2. **Pin the base.** `git merge-base origin/main HEAD` once, and give the reviewer that SHA. A branch-name diff pulls in unrelated upstream changes when the base has moved.
3. **Be honest about what you could not run and why.** That is where the reviewer should dig.
4. **Wait for the report** before telling the user the work is done. Meanwhile do only work the report cannot invalidate.

## Prompt

Fill the brackets. Keep the guardrail verbatim; it stops the pass from turning into a rewrite.

> This is a REPORT-ONLY pass on work I just finished. Do NOT edit files and do NOT propose scope expansion, large refactors or new features. Keep every suggestion small and concrete (`path:line` and the change). "Nothing found" is a valid, expected answer; do not invent problems.
>
> Context: [1 to 3 sentences, what and why, link to the issue or PR]. Worktree [path], base [SHA]. Diff: `git diff [SHA]..HEAD`; read surrounding code as needed.
>
> Task 1, verify the load-bearing invariants. [3 to 6 correctness claims the change rests on.] Also check the three Core Invariants in AGENTS.md (entropy is random, keys stay safe, what you see is what you sign) and say for each whether the change touches it and, if so, why it holds. For each claim, does it hold? If not, give a concrete failure scenario (inputs and state, wrong outcome). I could NOT run [what] because [why]. Trace it end to end and say whether it is correct and whether it could silently false-pass or hang.
>
> Task 2, simplify. Look only at [changed files]. Where is this more complex than the property requires? For any new test: is it flaky, or could it pass for the wrong reason? Suggest the minimal trim.
>
> Task 3, same-shape variant hunt. We fixed these bug shapes: [shape A]; [shape B]. Look narrowly, near the blast radius, for other live instances. If a shape turns up nothing, say "shape X: nothing found."
>
> Report each finding as: **[severity] path:line, one-line claim**, then the failure scenario and a confidence (likely real, possible, probably fine). HIGH = wrong result or fund-relevant on a live path; MEDIUM = latent or needs an unlikely precondition; LOW = nit. Most severe first, tight.

Scope: trivial change, skip or Task 1 only. Standard change, all three. Audit or fund-relevant code, all three, and if the variant hunt is rich, run it as its own sweep instead of cramming it in.

## Acting on the report

1. **Verify each finding against the code yourself** before touching anything. Confirm the failure scenario reproduces.
2. **Fix confirmed HIGH findings now**, in scope, with a regression test that fails without the fix.
3. **Assess MEDIUM honestly.** Some dissolve under scrutiny (the path is unreachable from real inputs). Then document the invariant at the site and move on. Dismiss with the reason, do not patch (see Managing Complexity in AGENTS.md).
4. **Apply in-scope simplifications.** Skip the ones that trade real coverage for brevity.
5. **Latent or out-of-scope findings: do not fix them here.** Record them and offer to file a follow-up. Filing a public issue is outward-facing, so confirm with the user first.
6. **The variant hunt often hands you the next fix.** A live instance on the same path is in-scope hardening, with its own test.
7. **Re-verify through the same reviewer** if your tool can message it again (send the fix delta, one line per finding on what you did). Otherwise do not re-run cold over a clean diff.

One pass is the rule. Re-run only if the fixes were large enough to need their own review. A review that keeps surfacing rare, unreachable scenarios is the complexity anti-pattern, not a reason to continue.
