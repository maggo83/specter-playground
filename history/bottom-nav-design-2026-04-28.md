# Bottom Navigation Design — Specter DIY GUI Rework

**Branch:** `Rework_Seedphrase_Wallet_BottomNavigation`  
**Date:** 2026-04-28  
**Status:** Agreed design — ready for implementation

---

## Screen Layout

```
┌──────────────────────────────────────┐
│  Top Bar              (STATUS_BAR_PCT%) │  ← context info + battery
├──────────────────────────────────────┤
│                                      │
│  Content Area         (CONTENT_PCT%) │  ← menus, action screens
│                                      │
├──────────────────────────────────────┤
│  Navigation Bar       (STATUS_BAR_PCT%) │  ← NEVER animated, always fixed
└──────────────────────────────────────┘
```

`STATUS_BAR_PCT = 8`, `CONTENT_PCT = 84` (unchanged from current codebase).

---

## Navigation Bar

### Purpose
Permanent visual anchor. Always visible, never animated, never scrolls away.

### Button Layout

Five icon slots, evenly spaced across the full width. Slot 3 (Home) is always
centered. When a slot's button is hidden, the remaining buttons **keep their
fixed positions** — they do not redistribute or collapse.

```
[Back]   [Seed]   [Home]   [Wallet]   [Device]
 pos 1    pos 2    pos 3    pos 4      pos 5
```

| Button | Icon (active/inactive) | Visibility | Tap action |
|--------|------------------------|------------|------------|
| Back | `CARET_LEFT` (always filled) | Only when not on home/main menu | Go back one history level (existing logic) |
| Seed | `KEY` filled / `KEY_OUTLINE` | Always | Toggle seed drop-up; or open it if closed |
| Home | `HOME` filled / `HOME_OUTLINE` | Always | Clear history → show main menu |
| Wallet | `WALLET` filled / `WALLET_OUTLINE` | Always | Toggle wallet drop-up; or open it if closed |
| Device | `GEAR` filled / `GEAR_OUTLINE` | Always | Toggle device/settings menu |

### Filled vs Outline (active state)

Reuses the exact same pattern as the `Rework_Seedphrase_Wallet_TopSelector`
branch (`HOME`/`HOME_OUTLINE`, `GEAR`/`GEAR_OUTLINE`).  
**New icons needed:** `KEY_OUTLINE` and `WALLET_OUTLINE` — to be generated from
the Bitcoin Icons SVG set, the same pipeline used for `home-outline.svg` →
`HOME_OUTLINE`, stored in `data/svg-outline-nav/`.

Active (filled) rules:
- **Home** is filled when `current_menu_id` is `"main"` (only main menu, not submenus)
- **Seed** is filled when the current menu belongs to the seed subtree
  (same frozenset pattern as `_SETTINGS_MENUS` in TopSelector)
- **Wallet** is filled when the current menu belongs to the wallet subtree
- **Device** is filled when the current menu belongs to the device/settings subtree
- **Back** is always displayed filled (CARET_LEFT, no outline variant needed)

### Drop-up Toggle Behavior (Seed / Wallet buttons)

- Tap when drop-up is **closed** → open the drop-up overlay
- Tap when drop-up is **open** → close it (toggle, same as Device button behavior)
- Tapping **Back** while a drop-up is open → close the drop-up
  (treated as a modal overlay, not pushed to navigation history)
- The drop-up is **not** a navigation history entry

---

## Top Bar

Always present. Contains context-dependent seed/wallet info.
Battery icon is **always** at the rightmost edge.

### Locked state
Battery icon only. No seed/wallet info shown.

### No seed loaded, or more than one seed loaded
Battery icon only (no other info).

### Exactly one seed loaded

Displayed left-to-right:
1. **Seed name** — dynamic font size (largest font that fits; same `_best_font_for_name` helper from TopSelector)
2. **Fingerprint** — `RELAY` icon (dummy, to be replaced with proper fingerprint icon when updated BTC icons land) + first 4 hex digits of fingerprint, **no** `0x` prefix
3. **Passphrase indicator** (optional) — only shown if a passphrase is set:
   - White `PASSWORD` icon → passphrase active
   - Grey `PASSWORD` icon → passphrase inactive
   - **Clickable** — tapping toggles `passphrase_active` (same as in the TopSelector seed bar `_toggle_passphrase_cb`)
4. **Backup warning** (optional) — orange `ALERT_CIRCLE` if seed is not yet backed up

#### Sub-cases for wallet section in the Top Bar:

**Only the default wallet loaded:**  
No further info beyond seed section.

**Exactly one non-default wallet loaded:**
5. **Separator** — `/` in a large font (visual divider between seed and wallet info)
6. **Wallet name** — dynamic font size (`_best_font_for_name`)
7. **Wallet type icon** — same as TopSelector: `KEY` (singlesig), `TWO_KEYS` (multisig), `CONSOLE` (custom script). If multisig, append `X/Y` threshold text (e.g. `2/3`). Color: white when signing keys loaded, grey otherwise.
8. **Account number** (optional) — shown only if `wallet.account != 0`, formatted as `#N`
9. **Network** (optional) — shown only if not mainnet: `"test"` / `"sig"` (mainnet is silent)

**More than one non-default wallet loaded:**
No further info beyond seed section (wallet section hidden).

### Name field sizing
Available space between fixed icon/label slots is computed dynamically.
`_best_font_for_name(text, max_w, max_h)` from TopSelector is reused:
tries `font_montserrat_28 → 22 → 16`, falls back to two-line split at word
boundaries if needed.

---

## Content Area

Unchanged in purpose. Renders the active menu or action screen.

---

## Seed / Wallet Drop-ups

### What is a drop-up?

A selection overlay anchored at the **top edge of the navigation bar**, growing
**upward**. Analogous to a Windows Start Menu or a mobile bottom sheet.
No animation required in this first iteration.

### Dimensions
- **Full screen width**
- Height: grows to fit content (number of list items), but **stops at the
  bottom edge of the Top Bar** — does not overlap the Top Bar
- If content exceeds that height, the list scrolls within the drop-up

### Overlay style
- Rendered above the Content Area (z-order overlay, not replacing it)
- A dim/transparent backdrop behind the panel is optional but recommended for clarity

### Seed drop-up content

One card per loaded seed, then an "Add Seed" button at the bottom.

Each seed card shows (left-to-right):
- **Seed name**
- **Passphrase indicator** — PASSWORD icon (white=active, grey=inactive), hidden if no passphrase set; **clickable** to toggle `passphrase_active`
- **Fingerprint** — RELAY icon + first 4 hex digits (no `0x` prefix)
- **Edit button** — EDIT icon, navigates to the seed manage menu

Grouping/sorting: same approach as current `SwitchAddSeedsMenu`.

### Wallet drop-up content

One card per registered wallet (including default), then an "Add Wallet" button at the bottom.

Each wallet card shows:
- **Wallet name**
- **Wallet type** — type icon (`KEY`/`TWO_KEYS`/`CONSOLE`) + threshold `X/Y` for multisig
- **Account number** — formatted as `#N`
- **Network** — `"main"` / `"test"` / `"sig"`
- **Edit button** — EDIT icon, navigates to the wallet manage menu

Grouping/sorting: same approach as current `SwitchAddWalletsMenu`.

**Note:** Unlike TopSelector, there is **no checkmark** showing the currently active element.

---

## Icon Assets Required

| Icon | Status | Action needed |
|------|--------|---------------|
| `HOME` / `HOME_OUTLINE` | ✅ Exists in TopSelector branch icons | Cherry-pick into this branch |
| `GEAR` / `GEAR_OUTLINE` | ✅ Exists in TopSelector branch icons | Cherry-pick into this branch |
| `EDIT_OUTLINE` | ✅ Exists in TopSelector branch icons | Cherry-pick into this branch |
| `CARET_LEFT` | ✅ Already in current branch | — |
| `KEY_OUTLINE` | ❌ Missing | Generate from Bitcoin Icons SVG set (`key-outline.svg` → `png-42/` → `key_outline.py`) |
| `WALLET_OUTLINE` | ❌ Missing | Generate from Bitcoin Icons SVG set (`wallet-outline.svg` → `png-42/` → `wallet_outline.py`) |

---

## Implementation Plan

1. **Cherry-pick icon assets** from TopSelector: `home_outline.py`, `gear_outline.py`, `edit_outline.py` + their `.svg` sources into `data/svg-outline-nav/`
2. **Generate** `key_outline.py` and `wallet_outline.py` from Bitcoin Icons SVGs
3. **Register** new icons in `btc_icons.py` (`KEY_OUTLINE`, `WALLET_OUTLINE`)
4. **Update stubs** — cherry-pick `Seed.passphrase_active`, `Seed.is_backed_up`, `Wallet.account` from TopSelector
5. **Build `NavigationBar`** — new widget replacing `WalletBar`. Five fixed-position buttons, filled/outline state logic, back-button conditional visibility, drop-up toggle
6. **Build `TopBar`** — new widget replacing `DeviceBar`. Battery always rightmost, seed/wallet contextual info, `_best_font_for_name` helper
7. **Build `SeedDropUp` / `WalletDropUp`** — overlay panels (non-animated), full-width, scroll if needed, card-per-item layout with edit button
8. **Update `SpecterGui`** — wire new bars in place of old ones, add context-set frozensets for active-icon logic, handle drop-up open/close state
9. **Update `main.py`** stub data — add `passphrase_active`, `is_backed_up`, `account` values for testing

---

## Open Questions / Decisions Made

| Question | Decision |
|----------|----------|
| KEY / WALLET inactive icon | Generate `KEY_OUTLINE` / `WALLET_OUTLINE` from Bitcoin Icons SVG set |
| Seed/Wallet drop-up toggle | Tap same button again → toggles closed |
| Back while drop-up open | Closes the drop-up (not a history nav event) |
| Drop-up max height | Grows upward, stops at bottom edge of Top Bar (no Top Bar overlap) |
| Wallet type display | Type icon + threshold `X/Y` for multisig (as in TopSelector) |
| Top Bar when locked | Battery icon only |
