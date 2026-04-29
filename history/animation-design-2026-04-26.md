# MockUI Animation Design — 2026-04-26

## Overview

This document captures the agreed animation spec before implementation.
It covers: screen regions that animate, context classification per menu-ID,
transition rules, and bar-caret behaviour.

---

## Screen layout (from top to bottom)

```
┌──-───────────────────────────────────┐
│  seeds_bar          (SELECT_BAR_PCT) │  row 0
├───-──────────────────────────────────┤
│  wallets_bar        (SELECT_BAR_PCT) │  row 1
├────-─────────────────────────────────┤
│                                      │
│  content area                        │  main animatable area
│                                      │
├─────-────────────────────────────────┤
│  device_bar         (STATUS_BAR_PCT) │  NEVER animated, always fixed
└─────────────────-────────────────────┘
```

Seeds_bar and wallets_bar are shown/hidden per context (see section 3).
`device_bar` is NEVER part of any animation.

---

## 1. Animatable regions (a / b / c / d)

| Region | What moves |
|--------|-----------|
| **a**  | Content area only (below wallets_bar if visible, else below seeds_bar) |
| **b**  | Wallets_bar + content area |
| **c**  | Seeds_bar + wallets_bar (if visible) + content area |
| **d**  | Seeds_bar only |

Key: "region" defines which LVGL objects are simultaneously animated.
In every horizontal animation the moved pixels are always full-height
(screen height minus device_bar) — there is NO y-shift during a left/right
slide.

---

## 2. Context classification

Every menu-ID belongs to exactly one context.
Bar visibility follows from the context (see section 3).

### DEVICE context
```
manage_settings
manage_security_settings, manage_security_features
manage_backups
manage_firmware
interfaces
manage_storage
select_language
manage_preferences
add_seed, generate_seedphrase        # no loaded seed ⇒ hide bars
change_pin, set_duress_pin, set_duress_pin_action
set_exceeded_pin_action, set_allowed_pin_retries
wipe_device, self_test
backup_to_sd, restore_from_sd, remove_backup_from_sd
update_fw_qr, update_fw_sd, update_fw_usb
internal_flash, sdcard, smartcard
display_settings, sound_settings
# any unrecognised ID opened from a device submenu → device context
```

### SEED context
```
switch_add_seeds
manage_seedphrase, store_seedphrase, clear_seedphrase
set_passphrase, show_seedphrase
store_to_smartcard, store_to_sd, store_to_flash
clear_from_smartcard, clear_from_sd, clear_from_flash, clear_all_storage
import_from_keyboard, import_from_qr, import_from_sd
import_from_smartcard, import_from_flash
```

### WALLET context
```
switch_add_wallets
add_wallet, create_custom_wallet
manage_wallet, manage_seed_wallet
manage_wallet_descriptor, change_network, view_signers
connect_sw_wallet
export_wallet
connect_sparrow, connect_nunchuck, connect_bluewallet, connect_other
import_wallet_from_qr, import_wallet_from_sd
```

### WALLET+SEED context  (main menu and its direct action screens)
```
main
scan_qr
view_addresses
connect_companion_app
start_intro_tour
# any unrecognised ID opened from main or wallet+seed → wallet+seed context
```

---

## 3. Bar visibility per context

| Context      | seeds_bar | wallets_bar |
|--------------|-----------|-------------|
| DEVICE       | hidden    | hidden      |
| SEED         | visible*  | hidden      |
| WALLET       | visible*  | visible*    |
| WALLET+SEED  | visible*  | visible*    |

`*` = visible only when the underlying data condition is met  
(`seeds_bar`: requires `active_seed is not None`)  
(`wallets_bar`: requires `active_seed is not None AND has_extra_wallet` (has_extra_wallet = active_wallet is not default wallet OR active_wallet.required_fingerprints is non-empty)).

The `_DEVICE_MENUS` frozenset maps directly to DEVICE context.  
A new `_SEED_MENUS` frozenset maps to SEED context.  
All other IDs are WALLET or WALLET+SEED as above.

---

## 4. Transition rules

### 4.1 Forward (push)

| From context | To context   | Region | Direction |
|--------------|--------------|--------|-----------|
| ANY          | DEVICE       | c      | horizontal → new (device) enters from right, old exits left |
| DEVICE       | ANY          | c      | horizontal → new enters from left, old (device) exits right |
| WALLET+SEED  | SEED         | b      | vertical  → new slides in from top (down), old content stays in place and new slides OVER it |
| WALLET+SEED  | WALLET       | a      | vertical  → new slides in from top (down), old content stays in place and new slides OVER it |
| SEED         | WALLET+SEED  | b      | vertical  → old exits upward revealing new beneath (new doesn't move, old lifts off) |
| WALLET       | WALLET+SEED  | a      | vertical  → old exits upward revealing new beneath (new doesn't move, old lifts off) |
| Within same context (any) | any submenu/action | a, b, or c (full content region for that context) | horizontal → new from right |

Notes:
- "Region c" always covers the full content (seeds + wallets + content), because
  in DEVICE context both bars are hidden anyway.
- "New slides over" means the old screen stays stationary; the new screen
  animates y from -(region height) → 0.
- "Old lifts off" means the new screen stays stationary; the old screen
  animates y from 0 → -(region height).
- When sliding in from the top, the new content start appearing beneath the content-relevant bar (not the screen top). I.e. for a switch to Seed context, the new content starts appearing beneath the seeds_bar (if visible). For a switch to Wallet context, the new content starts appearing beneath the wallets_bar.

### 4.2 Back (pop)

LVGL y-axis note: y=0 is the top of the screen; positive y goes downward.
- "Exits upward" = y animates from 0 → -(region_h)  (off the top)
- "Slides down into place" = y animates from -(region_h) → 0

All back transitions are the spatial mirror of the corresponding forward transition:

| Forward was | Back |
|-------------|------|
| horizontal right (new from right, old exits left) | horizontal left — new enters from left, old exits right |
| vertical "new slides down over old" (new: y -(h)→0; old stationary) | vertical "old exits upward, revealing new behind it" — old: y 0→-(h); new was stationary at y=0 behind old all along |
| vertical "old lifts off" (old: y 0→-(h); new stationary under old) | vertical "new slides down over old" — new: y -(h)→0; old stationary |

In other words back = invert both direction and the slide-over vs reveal-under
logic.

### 4.3 Same context (horizontal)

Applies to:
- Within DEVICE: submenu navigation
- Within SEED: submenu navigation (region = below seeds_bar)
- Within WALLET: submenu navigation (region = below wallets_bar)
- Within WALLET+SEED: submenu / action screen navigation (same region)

New screen slides in from the right; back slides in from the left.

---

## 5. Bar-caret transitions

### 5.1 Wallet bar ◀ / ▶

Shifts region **b** (wallets_bar + content area) in the caret direction:
- ▶ pressed → new content enters from right
- ◀ pressed → new content enters from left

seeds_bar stays fixed (it is outside region b).

### 5.2 Seed bar ◀ / ▶

Two cases:

**Case A — wallet stays the same** ("wallet fits new seed"):  
Condition: `active_wallet` is NOT the default wallet AND the new seed's
fingerprint is in `active_wallet.required_fingerprints`  
→ Shift region **d** only (seeds_bar slides), content and wallets_bar stay.  
Note: wallets_bar and content do **not** animate, but they must still be
refreshed/re-rendered in place to reflect the newly active seed (e.g. updated
fingerprint label, seed-specific wallet list).

**Case B — wallet changes** (default wallet or wallet does not fit new seed):  
→ Shift region **c** (seeds_bar + wallets_bar + content) in the caret direction.

The helper `state.seed_matches_wallet(new_seed, active_wallet)` already
implements the fit check.  The default wallet check is `wallet.is_default_wallet()`.

---

## 6. Animation mechanics (LVGL)

### Slide-over technique (vertical transitions)

For "new slides over old":
```
old_screen: set_pos(0, 0); does NOT animate (stays fixed)
new_screen: set_pos(0, -region_h); animates set_y from -region_h → 0
```

For "old lifts off" (reverse):
```
new_screen: set_pos(0, 0); does NOT animate (stays fixed, was already there)
old_screen: animates set_y from 0 → -region_h
```

### OVERFLOW_VISIBLE

`SpecterGui` (the root `lv.obj`) has `OVERFLOW_VISIBLE` set permanently in
`__init__` so device_bar layout is never disturbed.  `self.content` also needs
`OVERFLOW_VISIBLE` during the animation (added in `_do_transition`, removed
in the cleanup timer callback).

### GC safety

All Python closures and `lv.anim_t` / `lv.timer` objects are stored in
`self._anim_refs` during the animation and cleared in `_on_done`.

### Cleanup timer

A `lv.timer_create(_on_done, ANIM_MS + 50, None)` fires after the animation
completes to:
1. Delete old_screen
2. Reset positions/sizes of bars
3. Set content to final y / height
4. Re-enable FLEX layout on content
5. Clear `_animating` flag

---

## 7. Proposed implementation changes to `specter_gui.py`

### 7.1 Helper: `_context(menu_id) → "device"|"seed"|"wallet"|"main"`

Replaces the old `_section()` function.  Uses updated `_DEVICE_MENUS` and
`_SEED_MENUS` frozensets.  WALLET IDs get a new `_WALLET_MENUS` frozenset.
Everything else → "main" (= WALLET+SEED).

### 7.2 Helper: `_transition_params(from_id, to_id) → (region, axis, new_from)`

Returns:
- `region`: `"a"` | `"b"` | `"c"` | `"d"`
- `axis`: `"horizontal"` | `"vertical"`
- `new_from`: `"right"` | `"left"` | `"top"` | `"bottom"`

Back navigation inverts `new_from` (and swaps slide-over vs reveal-under).

### 7.3 `_do_transition(region, axis, new_from)`

Signature changes to accept the three parameters above.

Determines which LVGL objects to include in the animation based on `region`:
- `a`: `[new_screen, old_screen]` (content children)
- `b`: `[wallets_bar, new_screen, old_screen]`
- `c`: `[seeds_bar, wallets_bar, new_screen, old_screen]`
- `d`: `[seeds_bar]`

For vertical transitions uses slide-over / reveal-under mechanics.
For horizontal transitions uses the existing x-slide.

### 7.4 `refresh_ui_animated(direction, region)` (seed/wallet bar carets)

Extended to accept `region` so the caller can specify `"b"` or `"c"` or `"d"`.

---

## 8. Complete menu-ID to context mapping (for review)

```
# DEVICE
manage_settings, manage_security_settings, manage_security_features,
manage_backups, manage_firmware, interfaces, manage_storage, select_language,
manage_preferences, add_seed, generate_seedphrase,
change_pin, set_duress_pin, set_duress_pin_action,
set_exceeded_pin_action, set_allowed_pin_retries,
wipe_device, self_test, backup_to_sd, restore_from_sd, remove_backup_from_sd,
update_fw_qr, update_fw_sd, update_fw_usb, internal_flash, sdcard, smartcard,
display_settings, sound_settings

# SEED
switch_add_seeds,
manage_seedphrase, store_seedphrase, clear_seedphrase, set_passphrase, show_seedphrase,
store_to_smartcard, store_to_sd, store_to_flash,
clear_from_smartcard, clear_from_sd, clear_from_flash, clear_all_storage,
import_from_keyboard, import_from_qr, import_from_sd,
import_from_smartcard, import_from_flash

# WALLET
switch_add_wallets,
manage_wallet,
manage_wallet_descriptor, change_network, view_signers,
export_wallet,
import_wallet_from_qr, import_wallet_from_sd

# WALLET+SEED  (main context)
main, scan_qr, view_addresses, connect_companion_app, start_intro_tour,
add_wallet, create_custom_wallet
connect_sw_wallet
connect_sparrow, connect_nunchuck, connect_bluewallet, connect_other,
```

---

## 9. Resolved decisions

- `manage_seed_wallet` — dropped from all sets (treat as unrecognised, inherits parent context).
- ActionScreen for unrecognised IDs: **inherit context of parent** (check `history[-2]` / last known menu in stack).

---

*Generated before implementation. Update this file if spec changes.*
