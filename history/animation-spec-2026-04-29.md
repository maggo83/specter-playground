# Animation Spec — Rework_Seedphrase_Wallet_BottomNavigation
Date: 2026-04-29

---

## Layout

```
┌──────────────────────────────── 480px ──────────────────────────────┐
│                                                                      │
│   CONTENT AREA (top-bar is part of each screen)   92% = 736 px     │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│   NAVIGATION BAR  8% = 64 px   — FIXED, NEVER ANIMATED             │
│   [Back]  [Seed]  [Home]  [Wallet]  [Device]                       │
└──────────────────────────────────────────────────────────────────────┘
```

The navigation bar is always on top of the Z-order. Animated content never overlaps it. Content is clipped to its bounds so anything below `y = CONTENT_H` is invisible.

---

## Contexts

Only the direct nav-bar entry points for each context are explicitly classified. All submenus inherit context from their nearest parent on the history stack, so adding new submenus never requires updating these sets.

| Context | Explicit entry points |
|---------|----------------------|
| **main** | `main`, `locked`, `start_intro_tour` |
| **seed** | `manage_seedphrase`, `switch_add_seeds`, `add_seed` |
| **wallet** | `manage_wallet`, `switch_add_wallets`, `add_wallet` |
| **device** | `manage_settings` |

Everything else (`view_addresses`, `scan_qr`, all submenus, generic action screens) inherits context from the nearest known parent on the history stack. Falls back to `'main'` only when history is empty.

---

## Animation Types

### H-overlay — Horizontal Overlay (within-context navigation)

Only the entering/exiting screen moves. Used for navigating between menus within the same context.

- **Forward (into submenu):** New screen slides in from right (`x: +W → 0`). Old stays.
- **Back (out of submenu):** Old screen slides out to right (`x: 0 → +W`). New (previous) is already at `x = 0`.

Duration: `ANIM_MS = 150 ms`

### H-push — Horizontal Push (device context entry/exit)

Both screens move simultaneously.

- **Enter device context:** New slides from `x: +W → 0`; old slides from `x: 0 → -W`.
- **Exit device context:** Old (device) slides from `x: 0 → +W`; new slides from `x: -W → 0`.

Duration: `ANIM_MS = 150 ms`

### V-overlay — Vertical Overlay (seed/wallet context entry/exit)

Only the entering/exiting screen moves. Nav bar clips any overflow.

- **Enter seed/wallet context:** New screen slides up from bottom (`y: +CONTENT_H → 0`). Old stays. New covers old.
- **Exit seed/wallet context:** Old screen slides down (`y: 0 → +CONTENT_H`). New (previous) is already at `y = 0`. Old slides away revealing new.

Duration: `ANIM_MS_VERTICAL = 300 ms`

---

## Transition Rules

**Core principle:**
- **Forward navigation**: animation type is determined by the **destination** context.
- **Back navigation** (Back button) and **Home navigation**: animation type is determined by the **source** context (the reverse of the entry animation).

| Direction | From context | To context | Animation | Behaviour |
|---|---|---|---|---|
| Forward | any | same (to root) | H-overlay back | pressing nav button while in sub-menu; sub-screen slides out right, root revealed |
| Forward | any | same (deeper) | H-overlay forward | new slides in from right |
| Forward | any | device | H-push enter_device | both move; device from right, old to left |
| Forward | any | seed or wallet | V-overlay enter | new slides up from below |
| Back / Home | same | same | H-overlay back | old slides out to right, new already in place |
| Back / Home | device | any | H-push exit_device | both move; device to right, new from left |
| Back / Home | seed or wallet | any | V-overlay exit | old slides down, new (previous) already in place |
| Home | main | main | none | already on home screen |

**Key rules:**
- Device context always uses horizontal push (both screens move), in both directions.
- Seed/Wallet context always uses vertical overlay in both directions: enter slides up, exit slides down.
- **Nav-button tap while in a sub-menu of the same context** (e.g. tapping Device while inside device settings): treated as a jump to the context root → H-overlay back (sub-screen slides out right, root is revealed). Distinguishable because the destination is an explicit context-root ID and history is non-empty.
- Back/Home is always the mathematical reverse of the forward animation that navigated INTO the current menu — determined purely by the current (source) context, not the destination.
- There is no special "main → anything" forward case. `show_menu("main")` (Home button) always clears history and uses the exit animation of the current context.

**Home button implementation:** `show_menu("main")` clears history and sets `current_menu_id = "main"` without pushing the current menu. This ensures Back after Home never returns to a previous menu. The exit animation is chosen based on the context of the old menu.

---

## Drop-Up Overlays (Seed / Wallet nav bar buttons)

Drop-ups are `ModalOverlay` panels anchored above the nav bar and constrained to the content area. They never extend below the nav bar.

- **Open:** Panel starts at `y = CONTENT_H` (invisible, clipped by bottom boundary) and slides up to its final anchored position. Duration: 300 ms.
- **Close:** Panel slides from final position back down to `y = CONTENT_H`. Modal is destroyed in the close callback after the animation completes. Duration: 300 ms.
- **Guard:** `toggle()` is a no-op if an animation is already running.

---

## Input Blocking

While any animation is running (`_animating = True`), **all user input must be dropped**:
- `show_menu()` returns immediately without changing state.
- Nav bar button callbacks (`_seed_cb`, `_wallet_cb`, `_home_cb`, `_device_cb`, `_back_cb`) check `gui._animating` and return early.
- Drop-up `toggle()` / `open()` / `close()` check `_animating` and return early.
- The `_animating` flag is set to `True` at the start of `_do_transition()` and cleared in the cleanup timer callback after the animation duration has elapsed.

---

## History Snapshotting (active seed/wallet per history entry)

### Motivation

The `SpecterState.active_seed` and `active_wallet` attributes represent a single global selection. When the user navigates across contexts (e.g. Seed 1 → Wallet 1 → Seed 2), pressing Back should restore not just the menu but also the `active_seed`/`active_wallet` that were in effect at that navigation point.

### Example

1. User has Seed 1, Seed 2, Wallet 1, Wallet 2 loaded.
2. Taps Seed → selects Seed 1 → seed menu opens (active_seed=Seed1, active_wallet=Default).
3. Taps Wallet → selects Wallet 1 → wallet menu opens (active_seed=Seed1, active_wallet=Wallet1).
4. Taps Seed → selects Seed 2 → seed menu opens (active_seed=Seed2, active_wallet=Default).
5. Presses Back → returns to wallet menu with **Wallet 1** restored.
6. Presses Back → returns to seed menu with **Seed 1** restored.

### Implementation

`UIState.history` entries change from plain strings to `(menu_id, active_seed, active_wallet)` tuples.

- `UIState.current_menu_id` remains a plain string (unchanged; all existing menu code uses this).
- `push_menu(menu_id, seed=None, wallet=None)` saves the snapshot alongside the menu_id.
- `pop_menu()` returns `(active_seed, active_wallet)` so `show_menu()` can restore them to `SpecterState` before building the screen.

---

## Implementation Plan

### Step 1 — `UIState` history snapshotting
- Change `history` list entries from strings to `(menu_id, seed_snapshot, wallet_snapshot)` tuples.
- Update `push_menu()`, `pop_menu()`, `clear_history()` signatures and logic.
- Update all call sites in `specter_gui.py`.

### Step 2 — Animation infrastructure in `specter_gui.py`
- Add module-level constants `ANIM_MS = 150`, `ANIM_MS_VERTICAL = 300`.
- Add context sets `_CTX_DEVICE`, `_CTX_SEED`, `_CTX_WALLET`.
- Add `_context(menu_id, history)` helper → `'device' | 'seed' | 'wallet' | 'main'`.
- Add `_transition_params(from_id, to_id, going_back, history)` → `(anim_type, direction) | None`.
- Add `_animating` flag and `_anim_refs` list to `SpecterGui.__init__`.
- Extract `_build_screen(current)` method from `show_menu()`.
- Refactor `show_menu()` to compute transition params, call `_do_transition()` or `refresh_ui()`.
- Add `_do_transition(anim_type, direction)` implementing:
  - `H-overlay`: only new screen moves horizontally.
  - `H-push`: both screens move horizontally.
  - `V-overlay`: only one screen moves vertically.
- Cleanup timer pattern (identical to reference branch): restore layout, delete old screen, clear `_animating`.

### Step 3 — Drop-up slide animation in `dropup.py`
- Add `lv.anim_t` slide-up animation to `_DropUp.open()`.
- Add `lv.anim_t` slide-down animation to `_DropUp.close()`, destroy modal in callback.
- Add `_animating` instance flag; guard `toggle()`.

### Step 4 — Smoke test in simulator
- Verify all context transitions render correctly.
- Verify back navigation reverses correctly (including seed/wallet state restoration).
- Verify drop-up open/close animation.
- Verify nav bar is never covered.

---

## Reference

The `Rework_Seedphrase_Wallet_TopSelector` branch contains a complete working animation implementation for a different GUI layout (top selector bars instead of bottom nav). Key differences from our branch:

| TopSelector branch | BottomNavigation branch (this spec) |
|---|---|
| `seeds_bar` / `wallets_bar` at top — animated with context | No top bars — only content area animates |
| Region system (`a`/`b`/`c`/`d`) for bar subsets | Single content region (nav bar never moves) |
| Drop-down overlays (slide from top) | Drop-up overlays (slide from bottom) |
| H-push only for device context | Same |
| V-overlay for seed/wallet | Same |

The animation mechanics (LVGL `lv.anim_t`, cleanup timer, `_animating` guard, `_anim_refs` keepalive) are directly reusable.
