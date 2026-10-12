---
name: codify
description: Turn an observed agent misbehavior, or a correction the user just gave, into a durable fix in the narrowest place that removes the failure mode (a test or check, an AGENTS.md rule, a change to the skill that was running, or a new skill). Tightens an existing rule before adding one so AGENTS.md does not bloat. Invoke when the user corrects something that could recur.
argument-hint: "[<what went wrong, or the rule to encode>]"
disable-model-invocation: true
---

# Codify

The failure this skill fights is the one it could cause: piling rules into AGENTS.md until none of them land. Every addition must earn its place, and tightening or moving an existing rule beats adding a new one.

## 1. Capture the incident

Write down three things before touching a file: what happened (quote the transcript or the user), what was wanted instead, and why it matters (wasted tokens, a wrong diff, a broken invariant). If guessing would produce a different rule, ask the user with the candidate readings as options.

## 2. Distill the rule

Generalize to the smallest rule that covers the incident without over-fitting. "Never add a retry in `foo.py`" is a diff; "do not add retries or special cases for a failure the design could eliminate" is a rule. One sentence a fresh agent can apply, plus one line of why. Check that it does not forbid something the user wants elsewhere.

## 3. Look for existing coverage

Grep AGENTS.md and `.agents/` for the topic.

- Nothing found: continue.
- A rule exists and was violated anyway: do not add a duplicate. Find out why it did not land (buried, vague, phrased as a suggestion, contradicted elsewhere, only loaded inside a skill that was not active), then sharpen it, move it earlier or promote it to a stronger home.
- A skill was running when it went wrong: the rule belongs in that skill, not in AGENTS.md.

## 4. Pick the home

Walk down and stop at the first fit:

1. **A check that enforces it**: a test, a lint, a git hook or a tool hook. The behavior is mechanical and checkable, so make the bad state unreachable instead of asking the model to remember.
2. **An AGENTS.md rule**: behavior-shaping and five lines or fewer. Add it to the section it belongs to.
3. **An existing skill or agent.**
4. **A new skill**: a multi-step procedure or reference material too long to be always-on. Keep SKILL.md to procedure, bulk in `references/`.
5. **A user-level memory note**: a preference with no do or don't attached.

If it spans two homes, do both, with the AGENTS.md line kept to one sentence that points at the other.

## 5. Write and verify

Rule first as an imperative, why in one line, an example only if the rule is easy to misread. After the edit, look for a section that became redundant, stale or longer than its value, and cut or condense it. Re-read as a fresh agent would and confirm the rule rules out the observed behavior.

Leave the change uncommitted for the user to review. Report in one short paragraph: the incident, the rule, where it landed and why, what was cut.

## Do not codify

- A one-off slip with no pattern. Wait for the second occurrence.
- Something the tool already enforces.
- A restatement of an existing line (tighten that line instead).
- A preference the user has not actually stated. Ask.
