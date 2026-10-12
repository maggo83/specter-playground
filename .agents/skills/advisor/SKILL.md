---
name: advisor
description: Consult a stronger-tier model from a cheaper session for a judgment call (before committing to a plan, after two failed attempts at the same fix, before a risky or irreversible change, or at a real fork between two designs). Returns a plan or a decision, never code. Use about once per task.
argument-hint: "[--tier=top|standard] <the question or decision>"
---

# Advisor

The cheap session does the work and a top-tier sub-agent is consulted rarely. The saving only exists if two things hold:

1. **The main session is not already on the top tier.** If it is, you are the advisor: say so, reason it through yourself and stop.
2. **The packet is relevant, not raw.** A sub-agent shares no context or prompt cache with you, so everything you send is cold cost. Cut what does not bear on the question and be thorough with what does.

## When to consult

- Before committing to a plan for a non-trivial task.
- After two failed attempts at the same fix.
- Before a risky or irreversible change (wide blast radius, public interface, deletion).
- At a genuine fork where the choice is load-bearing.

Do not consult for things you can verify by reading the code, routine edits, style questions, or anything where you would accept your own first answer. Over-consulting is the failure mode: it makes the cheap session expensive.

A question only the user can settle (preference, scope) is not an advisor question. Ask the user, see Decision Checkpoints in AGENTS.md.

## Procedure

1. **Pick the tier.** Default `top`. Use `standard` for a moderate question. Say which in one line.
2. **Assemble the packet.** Read the relevant files first so you can hand over real excerpts:
   - Situation: the task, what you tried, exactly how each attempt failed, the constraints and invariants.
   - The question: one precise, answerable question.
   - Evidence: `path:line` excerpts with enough surrounding context to reason about.
   - What you want back: a plan, a decision with a one-line rationale, or what you are missing.
3. **Spawn one read-only sub-agent** on the chosen tier with this prompt, then the packet:

   > You are a senior advisor consulted by a cheaper model that does the actual work. Return terse, high-leverage guidance: a plan, a decision with a one-line rationale, or the specific thing the executor is missing. Do not write the implementation. Rank your points. If the executor's framing is wrong, say so first.

   If your tool lets you message the sub-agent again, keep it for follow-ups on the same task and send only the delta. Otherwise respawn with a one-paragraph summary. Do not reuse one advisor across unrelated tasks.
4. **Relay, do not dump.** Summarize the guidance in a few lines (decision, reason, steps) and act on it. You own the decision; discard an answer that is generic or tries to write the code.
