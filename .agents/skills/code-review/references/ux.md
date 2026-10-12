# UX and UI lens

For screens, components, themes, motion and texts shown to the user. Each item is a question to answer from what the screen actually renders (see Evidence), not from the code alone. Mark it OK, ISSUE or NOT APPLICABLE.

What the user sees for any fund-relevant action is governed first by Core Invariant 3 in AGENTS.md. A UX preference never outranks it.

## Sources and what we took

| Source | Status |
|---|---|
| [emilkowalski/skills](https://github.com/emilkowalski/skills) (MIT): `emil-design-eng`, `find-animation-opportunities`, `animation-performance`, `break-ui` | Principles taken, web specifics dropped |
| The `apple-design` skill of the same repo, a distillation of Apple's WWDC talks (*Designing Fluid Interfaces*, the design-principles talks, *Designing Audio-Haptic Experiences*, *The Details of UI Typography*) | Principles taken; the original talks were not re-watched, so check a rule against its talk before quoting it as Apple's |
| This project (hardware wallet, small touch display, LVGL on MicroPython) | Added: fund-relevant actions, i18n and legibility, accessibility, worst-case data, hardware limits |

Dropped because they do not apply here: Swift, React, Framer Motion, CSS and browser APIs (`transition`, `clip-path`, `backdrop-filter`, WAAPI, pointer capture, `@starting-style`), hover states (touch only), `/mobile-native` web fixes, UI library picking, the toast library, system fonts and dynamic type, velocity-projecting springs (LVGL scrolling already has momentum; a custom spring engine costs more than it gives), blur and translucent materials (cost on this hardware until measured), stagger entrances.

## 1. Purpose and simplicity

- Does every element earn its place? Is the common path first, with advanced options one level deeper?
- Is the most important thing the most obvious (order, spacing, contrast)? Is hierarchy built from weight, size and spacing together, not size alone?
- Are labels direct and specific ("Seeds", "Sign transaction") rather than vague umbrellas? If a control needs a label to explain its effect, the mapping is weak: place controls near what they affect.
- Is the language plain, without jargon, with fewer steps where possible?

## 2. Response and feedback

- Does the press show feedback at touch-down (pressed state), not only on release? Is anything on the input path adding latency (timers, waits)?
- During a drag or scroll, does the content follow the finger 1:1 and respect where it was grabbed?
- Feedback comes in four kinds. Is each present where needed: status (ongoing), completion, warning (before a problem), error (what went wrong and what to do)?
- Is validation inline, at the field, not only on submit?
- Taps: is there some tolerance around the target and can the user cancel by dragging away? A swipe needs a small movement threshold before it is committed.

## 3. Navigation and consistency

- Wayfinding: does every screen answer where am I, where can I go, what is here, how do I get out? Is the user ever trapped?
- Do things that look the same behave the same and sit in the same place (back, confirm, cancel)?
- Spatial consistency: a screen or panel that slides in from a side leaves toward the same side. Popovers and drop-ups originate from their trigger; modals stay centered.
- Forgiveness: easy back and undo for slips. Confirmations only for irreversible or fund-relevant actions, because a confirmation that appears everywhere trains people to click through (and a signing confirmation must never be that one).

## 4. Fund-relevant actions (project specific)

- What is shown for confirmation is factually correct and is what gets signed (Core Invariant 3). Check what the screen renders, not what the variable holds.
- Never truncate amounts, units, fees or anything the user compares. Give them the room, or paginate, but never shorten silently.
- Addresses, hashes and xpubs differ in the middle and at the end: when they cannot fit, do not end-truncate. Show them in groups, or truncate in the middle only together with a way to see and verify the full value.
- Secrets (seed words, PIN, passphrase) appear only where the user asked for them, only as long as needed, and input feedback does not leak them (Core Invariant 2).
- Is an irreversible action clearly worded and distinguished from a harmless one, and is the dangerous choice never the default?
- Error and recovery paths for these actions are as designed as the happy path.

## 5. Text, i18n and legibility (project specific)

- All strings go through i18n; no sentences assembled from fragments, no hard-coded text. There are two languages today (English, German); German is longer, so test with it.
- Layout survives longer translations and other scripts. Check the font actually covers the characters a language needs.
- Plural and zero forms are correct ("1 wallet", "0 wallets"); numbers, units and dates are formatted consistently.
- Contrast and size are legible at arm's length on the real display, in every theme. Color is never the only carrier of meaning (state, error, selection).
- Touch targets are comfortably tappable with a finger. TODO: fix the minimum size once measured on the real display, then add it here.

## 6. Worst-case data

Test with the worst realistic data, not the demo data the screen was designed against. Values are plausible or the real limit of the field (name length limits, list sizes), never random noise.

- Long names and labels (also translated), very short names, names with non-Latin characters and emoji.
- Empty list, exactly one item, and the realistic maximum (many seeds, wallets, accounts), including scrolling and memory behavior.
- Missing optional fields: no orphaned dashes or empty lines where a value was.
- Per field decide: wrap (things needed in full to identify something), truncate at the end (secondary metadata, with a way to see the rest), truncate in the middle (items that differ at the end), clamp lines (previews), never truncate (amounts and anything compared).
- States: card removed or missing, locked, not yet synced, error.
- Start the simulator from a preset with these values. Only `dev` exists today; a worst-case preset is a good addition (see [README](../../../../README.md#mockui) for presets).

Report breaks as Broken (unreadable, unreachable action, wrong data shown), Ugly (readable but visibly wrong), Fragile (fine now, one realistic step from breaking). Propose a fix for each and stop; design decisions (wrap or truncate) go to the user.

## 7. Motion

The goal is understanding, not decoration. Default to no animation and add one only if it passes the gate.

**Gate** (all four, in order, record the answer):

1. Frequency: used many times per session (core navigation, list scrolling, key entry)? Then no animation, or imperceptible. Occasional (modals, drawers, settings)? Eligible. Rare or first-time (onboarding, success, empty state)? This is where delight is allowed.
2. Purpose, named: feedback (the device heard the touch), spatial consistency (where something came from or went), state indication, or preventing a jarring change (content that teleports). "It looks cool" is not a purpose.
3. Speed: stay short. Starting values from the source, to tune on the board: press feedback 100 to 160 ms, small popovers 125 to 200 ms, drop-downs 150 to 250 ms, modals and drawers 200 to 500 ms, nothing routine over about 300 ms.
4. Function: data the user must read or act on (amounts, addresses, the transaction being confirmed) does not move for style.

**Parameters**

- Easing: ease-out for things entering or leaving (responds at once), ease-in-out for things moving on screen, linear only for constant motion (progress). Avoid ease-in on UI: it starts slow and feels laggy. Check which LVGL path each animation uses.
- Do not grow something from nothing; start from a partial size or position, with a fade where that is cheap.
- Exit is faster than enter. Slow where the user is deciding, fast where the system responds.
- Interruptible: never lock input during a transition; a tap during motion is handled, and a reversal starts from the current position, not the target.
- A theme sets the animation duration (`ANIM.HORIZONTAL`, `ANIM.VERTICAL`), and there is a user setting to turn animations off. The setting must really remove movement, and screens must stay clear without it. When off, keep a short fade or an instant change that still shows what changed; do not just drop the state change.

**Performance on this hardware**

- The simulator proves nothing about frame rate on the board. A smooth simulator run is not evidence; measure on the board, with the user's approval for the board (see AGENTS.md).
- Animate few and small things: position of one object, not a full-screen redraw or many objects at once. Large alpha blends and big areas are suspect until measured.
- Avoid per-frame allocation in animation callbacks (MicroPython heap).
- Review motion in slow motion: temporarily multiply the theme duration by 3 to 5 and look for stutter, wrong origin and out-of-sync pieces. Look again the next day; flaws show with fresh eyes.

**Finding opportunities**: sweep the screens for teleporting content, missing press feedback, panels with no connection to their trigger. Cap the list at 5 to 7 suggestions, order by leverage, give exact values, and always list 2 to 5 candidates you rejected with the gate question that rejected them. An empty list is a good result.

## 8. Accessibility

- Reduced motion: see section 7.
- Contrast in every theme; no information by color alone.
- Text size legible without squinting; layout does not break when text is longer.
- No flashing, no large fast-moving areas, no abrupt brightness jumps when switching themes.
- Feedback by sound or vibration, if the hardware ever has it: only on causal events, in step with the visual, and only where it earns its place. TODO: confirm what the hardware supports.

## 9. Visual consistency

- Colors, fonts, spacing and radii come from the theme layer, not hard-coded per screen; the screen looks right in every theme (`scenarios/MockUI/src/MockUI/basic/theming/themes/`).
- Nothing is random: every spacing, size and timing is a value you can defend. Misaligned icons and uneven spacing read as carelessness.
- Consistency with existing screens beats local cleverness. A deviation from a familiar pattern needs a reason and a test with users.

## Evidence

Judge screens from what they render, not from the code alone.

- The simulator and board are driven through specter-devtools; see [Visual Validation](../../../../devtools/docs/control-contract.md#visual-validation) for how to capture and compare screenshots, and "Simulator and Hardware Control" in AGENTS.md for when to use the simulator and the board.
- `specter-devtools --target simulator explore docs/MockUI/screens` refreshes the screenshots in [docs/MockUI](../../../../docs/MockUI/index.md).
- Say what was verified: from code, in the simulator, or on the board.

## Report format

A table, one row per issue, worst first: screen and element, section violated, evidence (screenshot or the value that broke it), severity (Broken, Ugly, Fragile), suggested change with the concrete value. Add a short list of what held up, so the reader knows what not to touch.
