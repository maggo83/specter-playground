# Python and MicroPython lens

Most code here runs twice: under CPython in pytest and under MicroPython on the simulator and the board. Review for both.

## Correctness and runtime parity

- Code that passes pytest on CPython can still fail on MicroPython: missing or different stdlib modules, no full `typing`, different exception text, integer and string method gaps, tighter memory. Check the construct is available in the MicroPython build (see `manifests/`) or has a fallback.
- Anything that depends on timing, the filesystem layout (`/flash`, SD), or hardware has a device-side test or is listed as not run.
- Exceptions: no bare `except:` that swallows errors, no `except Exception: pass`; catch the narrowest type and keep the context.
- Mutable default arguments, late-binding closures in loops, and shared module-level state across screens are common bug shapes here.

## Memory and performance (MicroPython heap)

- Allocation in hot paths (redraw, event handlers, loops) fragments the heap and triggers GC pauses. Reuse buffers, avoid building strings or lists per frame.
- Large `bytes` concatenation in loops, unbounded lists, caches without a size limit.
- Objects created per screen are deleted or reused; memory does not grow with navigation.
- Prefer measured evidence (free heap before and after) over assumption for a performance claim.

## LVGL and UI code

- Callbacks do not hold references to deleted objects; event handlers are not registered twice.
- Style and theme values come from the theme layer, not hard-coded per screen.
- User-visible strings go through i18n; no concatenated sentence fragments that cannot be translated.

## Design (see Managing Complexity in AGENTS.md)

- Does the design make the bad state unrepresentable, or does it add a flag or special case to cope with it?
- New abstraction with one implementation, a function over about 50 lines, nesting beyond three levels, copy-paste of an existing helper, a second source of truth for a fact.
- Names and structure match the surrounding code; a deviation is justified.

## Testing

- Tests assert behavior, not implementation; each has at least one assertion that can fail.
- Boundary values, equivalence classes and state transitions are covered, including the negative cases.
- No over-mocking that hides the real behavior; no sleep-based timing.
- New logic has a test in `scenarios/MockUI/tests/` (the pytest root, see `pytest.ini`). Anything only testable on the board goes under `scenarios/MockUI/tests_device/` and is named as not run when the board is absent.
- Parsers and decoders get malformed-input tests; add property-based or fuzz tests if the dependency is already available, otherwise ask before adding a dependency.
