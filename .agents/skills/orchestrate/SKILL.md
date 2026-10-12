---
name: orchestrate
description: Split a task that decomposes into independent items (multi-file refactor, N similar edits, a broad audit sweep) across sub-agents. A top-tier planner decomposes, cheap workers execute in parallel, the planner synthesizes. Opt-in only, invoke by name; sequential or single-file work does not need it.
argument-hint: "[--planner=top|standard] [--worker=cheap|standard] [--isolation] <task>"
disable-model-invocation: true
---

# Orchestrate

The expensive model is scarce (one planning pass, one synthesis pass) and the cheap model is abundant (N parallel workers). Most tokens are produced at the worker rate. This is the inverse of `advisor`.

It spends real tokens as soon as it runs, so it never fires on its own.

## Phase 0: scope and work-list (you, the main session)

1. Parse the tiers. Defaults: planner `top`, workers `cheap`. Use `standard` workers for anything that needs judgment. Use `--isolation` only if workers edit files that could collide (separate git worktrees or strictly disjoint file sets); otherwise skip it, worktrees are expensive.
2. **Scout inline first.** List the files, find the call sites, scope the diff. If the work-list is already obvious (one item per file over a known set), skip the planner and go straight to Execute.
3. Do not fan out what you have not scoped. A planner guessing at structure wastes the expensive stage.

## Phase 1: plan (top tier, only if the list is not obvious)

One sub-agent: "Decompose this task into independent work items, each self-contained with no cross-item context needed. Return a compact list: id and spec per item." Prose output means the slice is wrong.

## Phase 2: execute (cheap tier, parallel)

One worker per item, all launched in a single message so they run concurrently. Each brief is self-contained: the item spec, the relevant paths, the constraints from AGENTS.md that apply, the done criterion, and the result format. Workers report; they do not coordinate.

## Phase 3: synthesize (top tier)

Hand the planner every worker result and ask for one coherent answer with conflicts and gaps flagged. Relay that answer, not the per-item output.

## Keep the expensive stages thin

- The planner must not read the codebase to build the plan. If decomposing needs deep reading, scout first or give that reading to a worker.
- The synthesizer stitches and flags; it does not redo worker work.
- Never skip synthesis and dump raw worker output.

If planner or synthesizer is doing token-heavy reading, the slicing is wrong and the work has quietly moved back to the expensive tier.

If your tool cannot run sub-agents in parallel or choose a model per sub-agent, say so and do the items sequentially yourself.
