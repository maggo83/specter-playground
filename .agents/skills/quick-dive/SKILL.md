---
name: quick-dive
description: Fast, targeted answer to one specific question about the code (how X works, where Y lives, what Z does). About 2 minutes, at most 10 files, no subagent fan-out. For a full architecture picture use deep-dive.
argument-hint: "<specific question about the codebase>"
---

# Quick Dive

Hand the question to the `code-scout` agent on a cheap tier. Its limits (files, depth, output size, no fan-out) are defined in `.agents/agents/code-scout.md`; do not restate them here.

If no sub-agent is available, answer yourself under the same limits.

Use it for "how does X work", "where is Y implemented", "what does this function do", navigation and debugging-session questions. Do not use it for full system documentation, multi-subsystem interactions, audits or dependency mapping. When the scout recommends escalation, switch to `deep-dive`.
