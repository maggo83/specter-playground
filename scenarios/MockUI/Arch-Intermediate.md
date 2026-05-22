# MockUI — Architecture Overview

_Reference documentation for the architecture of `scenarios/MockUI/src/MockUI/`._

---

## 1. Purpose

MockUI is the new Specter device GUI written for LVGL 9.3 on MicroPython.
It is a self-contained Python package that runs both on the F469 hardware
target and on the unix simulator. All hardware-side behaviour is still stubbed
through small in-memory data classes so the UI layer can be developed and
exercised independently.

The package is organised in four conceptual layers:

| Layer | Folder(s) | Responsibility |
|-------|-----------|----------------|
| Application | `basic/specter_gui.py` | Root controller; owns screen, navigation bar, i18n, keyboard. |
| Screen / view framework | `basic/` (except widgets) | Reusable screens, menus, navigation, drop-ups, animations, context bar. |
| Widgets | `basic/widgets/`, `basic/symbol_lib/` | Atomic LVGL builders (buttons, labels, containers, modals, icons). |
| Data / domain stubs | `stubs/`, `i18n/`, `fonts/` | In-memory device/seed/wallet state, translations, font loading. |

Feature folders (`seed/`, `wallet/`, `device/`, `tour/`) plug concrete views
on top of those layers.

---

## 2. Package Layout

```
MockUI/
├── __init__.py
├── basic/                    UI framework
│   ├── ui_consts.py          screen/colour/font/spacing constants
│   ├── ui_utils.py           cross-cutting helpers (configure_as_bare, …)
│   ├── animations.py         slide_x / slide_y / GUIAnimations constants
│   ├── specter_gui.py        SpecterGui — root controller
│   ├── specter_gui_base.py   SpecterGuiMixin / SpecterGuiElement bases
│   ├── app_screen.py         AppScreen (content + battery + context_bar)
│   ├── titled_screen.py      TitledScreen (title_bar + body, title-delete helper)
│   ├── action_screen.py      ActionScreen (placeholder for unmapped menu IDs)
│   ├── menu.py               GenericMenu (template method) + helpers
│   ├── main_menu.py          MainMenu (home screen)
│   ├── locked_menu.py        LockedMenu (PIN entry)
│   ├── navigation_bar.py     persistent bottom nav bar
│   ├── context_bar.py        seed/wallet context strip at top
│   ├── dropup.py             SeedDropUp / WalletDropUp bottom sheets
│   ├── confirm_modals.py     confirm_delete_seed / _wallet
│   ├── keyboard_manager.py   on-screen keyboard controller
│   ├── keyboard_layouts.py   ALNUM / FULL key-map definitions
│   ├── symbol_lib/           Icon class + auto-generated BTC_ICONS
│   └── widgets/              atomic LVGL widget helpers
│       ├── btn.py            Btn (icon + label button wrapper)
│       ├── battery.py        Battery indicator
│       ├── containers.py     flex_row / flex_col / dialog_card / strips
│       ├── labels.py         body_label / section_header / form_label / make_label
│       ├── inputs.py         title_textarea and other text-area builders
│       ├── icon_widgets.py   make_icon + set_visible helper
│       ├── menu_item.py      MenuItem + MenuItemSuffix data classes
│       ├── modal_overlay.py  ModalOverlay (layer_top backdrop+overlay base)
│       ├── action_modal.py   ActionModal (generic confirm/choice dialog)
│       ├── card_helpers.py   build_card_row + slot helpers
│       ├── seed_widgets.py   build_seed_card, fingerprint_badge, …
│       └── wallet_widgets.py build_wallet_card, wallet_net_text, …
├── stubs/
│   ├── ui_state.py           UIState + Context constants
│   ├── device_state.py       DeviceState (battery, locked, loaded seeds, …)
│   ├── seed.py               Seed
│   └── wallet.py             Wallet + WalletType + helpers
├── i18n/
│   ├── i18n_manager.py       runtime translation manager
│   ├── translation_keys.py   KEY_TO_INDEX + Keys constants (build product)
│   ├── lang_compiler.py      JSON→binary compiler (build-time tooling)
│   └── languages/            *.json sources, *.bin compiled
├── fonts/                    font loader modules
├── seed/                     seed-management menus (7 files)
├── wallet/                   wallet-management menus (5 files)
├── device/                   device-settings menus (9 files)
└── tour/                     first-run guided tour
    ├── guided_tour.py        GuidedTour + INTRO_TOUR_STEPS
    └── ui_explainer.py       UIExplainer overlay with arrow/cutout
```

---

## 3. Class Hierarchy

```
lv.obj
└── SpecterGui                root controller (basic/specter_gui.py)
    └── AppScreen             screen container with content + battery + context bar
        └── TitledScreen      title_bar + body; base for every view
            ├── GenericMenu   template-method menu builder
            │   ├── MainMenu, LockedMenu
            │   ├── seed/*  (AddSeedMenu, SeedPhraseMenu, RelatedWalletsForSeedMenu,
            │   │            StoreSeedphraseMenu, ClearSeedphraseMenu, …)
            │   ├── wallet/* (WalletMenu, AddWalletMenu, ConnectWalletsMenu,
            │   │             ViewSignersMenu)
            │   └── device/* (SettingsMenu, SecuritySettingsMenu, BackupsMenu,
            │                 FirmwareMenu, InterfacesMenu, StorageMenu,
            │                 SecurityFeaturesMenu, LanguageMenu,
            │                 PreferencesMenu)
            ├── GenerateSeedMenu, PassphraseMenu, CreateCustomWalletMenu
            │   (form-style views built manually, not via GenericMenu)
            └── ActionScreen  fallback view for unmapped menu IDs

lv.obj (separate trees)
├── NavigationBar             persistent bottom bar, owned by SpecterGui
├── ContextBar                top strip when a seed/wallet is active
└── ModalOverlay (layer_top)
    ├── ActionModal           confirmation / choice dialogs
    ├── SeedDropUp / WalletDropUp   bottom-sheet selectors
    └── UIExplainer           guided-tour highlight overlay
```

Non-widget controllers that still need to read `gui.device_state`, `gui.t`,
etc. inherit from a pure-Python base instead:

```
SpecterGuiMixin (pure Python)
├── _DropUp → SeedDropUp, WalletDropUp
└── GuidedTour, KeyboardManager (use gui directly, not via the mixin)
```

`SpecterGuiMixin` and `SpecterGuiElement` carry the same set of read-only
properties (`device_state`, `ui_state`, `context`, `active_seed`,
`active_wallet`, `i18n`, `t`, `on_navigate`, `keyboard_manager`,
`current_menu`). The properties are installed onto each class by a shared
``_install_gui_properties`` helper in `specter_gui_base.py`, so the
accessors only exist in one place. The two classes still exist because
MicroPython does not support multiple inheritance — `SpecterGuiElement`
extends `lv.obj` while `SpecterGuiMixin` is a plain Python base.

---

## 4. Core Patterns

### 4.1 Navigation: stack + dict dispatch

`SpecterGui.navigate_to(target_menu_id, target_seed, target_wallet)` is the
single entry point for view changes. It:

1. Updates `UIState.history` (push, pop, or `clear_history`) and obtains an
   `anim` constant.
2. Optionally updates `active_seed` / `active_wallet`.
3. Either animates the transition (`_do_transition`) or rebuilds the screen
   directly when animations are disabled.
4. Calls `refresh_ui()`.

Going "back" is signalled by `target_menu_id` being `None` or `"back"`.

`_build_view(screen, menu_id)` maps the current menu ID to a view class via
the `_VIEW_MAP` dict (24 entries). Unmapped IDs fall back to `ActionScreen`,
which acts as a developer placeholder.

### 4.2 Context system

`stubs/ui_state.Context` defines six integer constants:

```
MAIN, DEVICE, ADD_SEED, SEED, ADD_WALLET, WALLET
```

The current context is derived from `current_menu_id` via the `_MENU_CONTEXT`
dict and stored in `UIState.active_context`. Context drives three things:

- The animation type returned by `push_menu` / `pop_menu`.
- Whether `AppScreen` builds a `ContextBar` at the top (only in SEED /
  WALLET with a non-`None` active seed/wallet).
- Which drop-up panel a tap on the nav bar opens (Seed vs Wallet).

### 4.3 `GenericMenu` template method

Every menu derived from `GenericMenu` implements one required hook and up to
three optional hooks:

```
get_menu_items(t, state) -> list[MenuItem]   # required
get_title(t, state)      -> str              # optional (overrides title)
pre_init(t, state)       -> None             # optional, before items are built
post_init(t, state)      -> None             # optional, after items are built
```

`fill_body()` runs the sequence:

```
items = get_menu_items(...)
pre_init(...)
_build_menu_items(items)
post_init(...)
_configure_scroll()
```

`_build_menu_items` recognises three shapes of `MenuItem` and renders each
accordingly:

| Shape | Rendered as |
|-------|-------------|
| No `target`, no `get_value`/`set_value`, no icon | Section header (visual separator). |
| `get_value` and `set_value` both set | Toggle row (`lv.switch`). |
| `target` set (menu-id string or callable) | Button row, optionally with `suffix`, `help_key`, `is_submenu` chevron. |

`rebuild_body()` is provided for menus that need to re-render after state
changes (e.g. when a seed list grows).

### 4.4 `MenuItem` data class

`basic/widgets/menu_item.py::MenuItem` is the single carrier between
`get_menu_items` and the renderer. Fields:

```
icon, text, target, color, size, help_key, suffix,
is_submenu, font_color, get_value, set_value
```

`MenuItemSuffix` is the companion class for right-aligned icon/label groups
inside a button (network badge, account index, etc.).

Modals share the same data class: `ActionModal(buttons=[MenuItem(...), ...])`
treats each button as a `MenuItem`-shaped object via duck-typed attribute
access.

### 4.5 Screen composition

A frame is built bottom-up:

```
SpecterGui (lv.obj root)
├── AppScreen                   one per visible view, swapped on navigation
│   ├── content (flex_col)      always present, fills available height
│   │   └── view = TitledScreen subclass
│   │       ├── title_bar       optional; hosts title label + delete button
│   │       └── body            menu items / form widgets
│   ├── context_bar             optional, SEED/WALLET only
│   └── battery                 optional, only when device_state.has_battery
└── NavigationBar               persistent, single instance owned by SpecterGui
```

The `AppScreen` decides at construction time (based on the active context)
whether to create a `context_bar` and a `battery`. Transitions can either
animate the entire `AppScreen` unit (cross-context navigation) or only the
inner `view` widget (within the same context, so the bars stay put).

### 4.6 Navigation bar + drop-ups

`NavigationBar` is a permanent five-slot bar (`Back, Seed, Home, Wallet,
Device`). Icons are filled/outlined based on the current menu ID (each slot
has a frozen set of "active" menu IDs).

The `Seed` and `Wallet` slots open `SeedDropUp` / `WalletDropUp` — bottom
sheets that grow upward from just above the nav bar. Both share one
`ModalOverlay` backdrop, created lazily on first open and released when both
panels are closed. The nav bar owns the full lifecycle of both drop-ups.

### 4.7 Context bar

When SEED or WALLET is active and an item is selected, `AppScreen` builds a
`ContextBar` strip showing the current seed or wallet. The strip is
constructed by `build_seed_card` / `build_wallet_card` from
`widgets/seed_widgets.py` and `wallet_widgets.py`, which share their layout
scaffolding through `widgets/card_helpers.py` (`build_card_row`,
`build_leading_icon_slot`, `build_name_slot`, `build_delete_slot`).

The card's name field is an editable text area. Tapping it routes through
`KeyboardManager.bind(...)` and commits a rename back into
`active_seed` / `active_wallet` on confirm.

### 4.8 Modals

All overlays inherit from `widgets/modal_overlay.ModalOverlay`, which
parents itself to `lv.layer_top()` and exposes a `close()` animation hook.

- `ActionModal` — generic dialog with text + button row.
- `confirm_modals.confirm_delete_seed` / `confirm_delete_wallet` —
  ready-made delete confirmations built on `ActionModal` with `MenuItem`
  buttons.
- `make_help_callback(...)` (in `basic/menu.py`) — help popup for items that
  carry `help_key`.

### 4.9 Keyboard

`KeyboardManager` (singleton per `SpecterGui`, attached at construction
time) handles the on-screen keyboard. Callers bind a textarea once and
provide `on_commit`, `sanitize` and `on_cancel` callbacks; the manager
opens/closes the keyboard and forwards events. Two layouts exist (`ALNUM`,
`FULL`), defined as nested tuples in `keyboard_layouts.py`.

### 4.10 Internationalisation

`I18nManager` loads compiled binary translations from
`i18n/languages/*.bin` and exposes `t(key, **fmt) -> str`. Every view
accesses translations via the `self.t` shortcut, which is a property on
both `SpecterGuiMixin` and `SpecterGuiElement` resolving to
`self.gui.i18n.t`. New languages can be added at runtime by compiling a JSON
file via `lang_compiler.json_to_binary`.

### 4.11 Guided tour

`tour/guided_tour.py::GuidedTour` plays a list of steps. Each step is a
tuple `(element_spec, i18n_key, position)`. `element_spec` may be `None`
(centred), a dotted attribute path resolved against the `SpecterGui` (e.g.
`"navigation_bar"`), or an explicit `(x, y, w, h)` rectangle.

`tour/ui_explainer.py::UIExplainer` renders the per-step overlay: a
semi-transparent backdrop with a cutout around the highlighted area and a
text bubble pointing at it. Cutout coordinates use LVGL's
`get_x_absolute()` / `get_y_absolute()`.

The tour is launched on first startup (gated by
`UIState.is_run_tour_on_startup`, persisted to
`/flash/ui_state_config.json`) and can also be re-entered from the device
settings.

---

## 5. Data Model (`stubs/`)

These classes deliberately stay in plain Python with no typing imports so
they work uniformly under MicroPython and CPython.

### `DeviceState`
Top-level device state. Holds battery (`has_battery`, `battery_pct`,
`is_charging`), lock state (`is_locked`, `pin`), loaded seeds (the in-RAM
list), saved seeds (the simulated NVRAM list), feature flags
(`_enabledQR`, `_enabledKeyboard`, …), and convenience methods such as
`lock()`, `unlock()`, `add_seed()`, `remove_seed()`,
`debug_cycle_battery()`.

### `UIState`
Navigation state, animation preferences and tour state.

- `history: list[Snapshot]` — LIFO stack of previous views, capped at
  `MAX_HISTORY_DEPTH`.
- `current_menu_id`, `active_context`, `active_seed`, `active_wallet` —
  current selection.
- `are_animations_enabled` — user preference.
- `push_menu(menu_id) → anim`, `pop_menu() → anim`, `clear_history() → anim`
  — return the animation type to play, or `None` for instant.
- `set_active_seed`, `set_active_wallet`.
- `is_run_tour_on_startup` plus persistence to a JSON config file.

### `Seed`
Mock seed object: name, mnemonic words, fingerprint, passphrase, derivation
paths, etc.

### `Wallet`
Mock wallet object: name, descriptor, type (`WalletType` enum-like class),
account index, network, signers list. Helper functions on the module
(`_wallet_type_rank` etc.) provide sort/ordering logic shared between the
wallet UI and the seed→wallets cross-reference views.

---

## 6. Folder-by-folder Summary

### `basic/`
The UI framework. Every screen-level abstraction lives here. The package
`__init__.py` re-exports the public surface used by feature folders and the
entry-point script.

### `basic/widgets/`
Stateless LVGL builders. Each module exposes small factory functions (e.g.
`flex_col(parent, ...)`, `body_label(parent, text, ...)`) that return
configured `lv.obj` instances. Heavier widgets (`Btn`, `Battery`,
`ActionModal`, `ModalOverlay`) are classes; everything else is a function.

### `basic/symbol_lib/`
Icon system. `icon.py::Icon` wraps an A8-format bitmap and acts as a
callable (`icon(color) → coloured copy`). `btc_icons.py` is an
auto-generated aggregator that exposes ~175 icons via a `BTC_ICONS`
namespace — do not edit by hand.

### `stubs/`
In-memory data classes (see §5). No UI imports.

### `i18n/`
Runtime translation manager plus a build-time JSON→binary compiler. The
binary format and the integer-indexed `Keys` constants live in
`translation_keys.py`.

### `fonts/`
Per-language font loader modules (e.g. `font_loader_de.py`). Pulls
LVGL-compiled `.bin` font files into globally available `lv.font_t`
handles.

### `seed/`
Concrete menus for seed management: `AddSeedMenu`, `SeedPhraseMenu`,
`StoreSeedphraseMenu`, `ClearSeedphraseMenu`, `GenerateSeedMenu`,
`PassphraseMenu`, `RelatedWalletsForSeedMenu`. Most extend `GenericMenu`;
`GenerateSeedMenu` and `PassphraseMenu` are form-style screens that extend
`TitledScreen` directly.

### `wallet/`
Concrete menus for wallet management: `WalletMenu`, `AddWalletMenu`,
`ConnectWalletsMenu`, `CreateCustomWalletMenu`, `ViewSignersMenu`.
`CreateCustomWalletMenu` is form-style; the rest are `GenericMenu`
subclasses.

### `device/`
Concrete menus for device settings: `SettingsMenu` (root), and the leaves
`SecuritySettingsMenu`, `BackupsMenu`, `FirmwareMenu`, `InterfacesMenu`,
`StorageMenu`, `SecurityFeaturesMenu`, `LanguageMenu`, `PreferencesMenu`.
All extend `GenericMenu`.

### `tour/`
First-run guided tour. `INTRO_TOUR_STEPS` is the canonical step list;
`GuidedTour` drives playback; `UIExplainer` renders each step's overlay.

---

## 7. Conventions

These conventions are enforced by example throughout the codebase:

- **`self.t` for translations.** Every view derives from
  `SpecterGuiElement` or `SpecterGuiMixin` and uses `self.t("KEY")` (and the
  `self.i18n`, `self.device_state`, `self.ui_state` shortcuts).
- **`self.on_navigate(...)`** for navigation, never `self.gui.navigate_to`
  directly. `on_navigate` is also exposed to callbacks via closure capture.
- **`MenuItem`** is the only argument shape for both `get_menu_items` and
  `ActionModal.buttons`.
- **`MicroPython.const`** in constants files (`ui_consts.py`,
  `ui_state.py`). Constants are then aliased into normal Python attributes
  on a wrapper class when grouped (`Context` mirrors `_MENU_CTX_*`).
- **No multiple inheritance.** Use the dual base classes
  `SpecterGuiMixin` / `SpecterGuiElement` depending on whether the consumer
  is a plain controller or an `lv.obj`.
- **`configure_as_bare(widget, ...)`** is the standard way to strip
  default LVGL chrome (padding, border, scrollbars) from a container.
- **`delete_all_children_of(widget)`** is the standard way to clear a body
  before rebuilding it.
- **Animations through `animations.slide_x` / `slide_y`** with `GUIAnimations`
  constants for direction selection.
- **Card layouts via `widgets/card_helpers.py`.** Seed/wallet cards in the
  context bar and drop-ups share `build_card_row` and the slot helpers.

---

## 8. Entry Points

The package exports a small public API from `MockUI/__init__.py`:

- `SpecterGui` — root widget; instantiate with optional `device_state` and
  `ui_state` arguments.
- `UIState`, `DeviceState`, `Wallet`, `Seed` — state classes for callers
  that want to inject pre-populated state (the simulator and tests do this).

Typical usage in a simulator scenario:

```python
gui = SpecterGui(specter_state=DeviceState(), ui_state=UIState())
gui.navigate_to("main")
```

Once constructed, `SpecterGui` installs a periodic `lv.timer` that calls
`refresh_ui()` at `GUI_REFRESH_MS` intervals. Navigation is driven by
`navigate_to()`, which any view can reach via `self.on_navigate(...)`.
