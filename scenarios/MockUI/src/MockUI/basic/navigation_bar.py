"""NavigationBar — permanent bottom navigation bar for Specter MockUI.

Layout (left-to-right, full width, STATUS_BAR_PCT% height):
    ┌────────────────────────────────────────────────────┐
    │  [Back]   [Seed]   [Home]   [Wallet]   [Device]    │
    │  pos 1    pos 2    pos 3    pos 4      pos 5       │
    └────────────────────────────────────────────────────┘

All five slots have fixed positions (SCREEN_WIDTH / 5 each).

Filled vs outline icon rules
─────────────────────────────
- Home   → filled when current_menu_id == "main"
- Seed   → filled when current_menu_id is in _SEED_MENUS
- Wallet → filled when current_menu_id is in _WALLET_MENUS
- Device → filled when current_menu_id is in _DEVICE_MENUS
- Back   → always filled (CARET_LEFT, no outline variant)

Drop-up wiring
──────────────
Call set_seed_dropup(obj) / set_wallet_dropup(obj) immediately after
construction to register overlay panels.  All button callbacks and
refresh() assume the drop-ups are present — they must be wired before
any user interaction or refresh call can occur.
"""

import lvgl as lv
from .ui_consts import (
    SCREEN_WIDTH, STATUS_BTN_HEIGHT, STATUS_BAR_PCT,
    GREY, WHITE,
)
from .symbol_lib import BTC_ICONS
from .widgets.btn import Btn
from .specter_gui_base import SpecterGuiElement
from .dropup import DropUpState

# ── Active-menu sets (frozensets for fast membership testing) ─────────────────
_SEED_MENUS = frozenset({
    "manage_seedphrase",
    "switch_add_seeds",
    "add_seed",
    "store_seedphrase",
    "clear_seedphrase",
    "generate_seedphrase",
    "set_passphrase",
    "manage_seed_wallet",
})

_WALLET_MENUS = frozenset({
    "manage_wallet",
    "view_signers",
    "switch_add_wallets",
    "add_wallet",
    "connect_sw_wallet",
    "create_custom_wallet",
})

_DEVICE_MENUS = frozenset({
    "manage_security_settings",
    "manage_security_features",
    "manage_backups",
    "manage_firmware",
    "interfaces",
    "manage_storage",
    "manage_settings",
    "manage_preferences",
    "select_language",
})

class NavigationBar(SpecterGuiElement):
    """Permanent bottom navigation bar with 5 fixed-position icon buttons."""

    def __init__(self, gui):
        super().__init__(gui)

        self.gui = gui

        # Drop-up panel references — wired via set_*_dropup() immediately after init
        self._seed_dropup = None
        self._wallet_dropup = None

        # ── Bar container style ───────────────────────────────────────────────
        self.set_width(lv.pct(100))
        self.set_height(lv.pct(STATUS_BAR_PCT))
        self.set_layout(lv.LAYOUT.NONE)   # absolute child positioning
        self.set_style_pad_all(0, 0)
        self.set_style_radius(0, 0)
        self.set_style_border_width(0, 0)
        self.set_scroll_dir(lv.DIR.NONE)

        h = STATUS_BTN_HEIGHT
        w = SCREEN_WIDTH // 5

        names = ["Back", "Seed", "Home", "Wallet", "Device"]
        icons = [BTC_ICONS.CARET_LEFT,
                 BTC_ICONS.KEY_OUTLINE,
                 BTC_ICONS.HOME_OUTLINE,
                 BTC_ICONS.WALLET_OUTLINE,
                 BTC_ICONS.GEAR_OUTLINE]
        cbs = [self._back_cb, self._seed_cb, self._home_cb, self._wallet_cb, self._device_cb]

        self.buttons = {}
        for i, (name, icon, cb) in enumerate(zip(names, icons, cbs)):
            self.buttons[name] = Btn(self, icon=icon, size=(w, h), callback=cb)
            self.buttons[name].make_background_transparent()
            self.buttons[name].align(lv.ALIGN.LEFT_MID, i * w, 0)

    # ── Drop-up wiring and management ────────────────────────────────────────────

    def set_seed_dropup(self, dropup):
        """Register the seed drop-up overlay panel."""
        self._seed_dropup = dropup

    def set_wallet_dropup(self, dropup):
        """Register the wallet drop-up overlay panel."""
        self._wallet_dropup = dropup

    def _close_dropup(self, dropup):
        """Close a specific drop-up."""
        if dropup.get_state() in (DropUpState.OPENING, DropUpState.OPEN):
            dropup.close()

    def _close_dropups(self):
        """Close any open drop-ups."""
        self._close_dropup(self._seed_dropup)
        self._close_dropup(self._wallet_dropup)

    # ── Guards ────────────────────────────────────────────────────────────────

    def _busy_or_not_init(self):
        """Return True if button taps should be ignored.

        This is the case when the drop-ups have not been registered yet
        (init not complete) or when a screen transition animation is running.
        """
        return (
            self._seed_dropup is None
            or self._wallet_dropup is None
            or getattr(self.gui, '_animating', False)
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def refresh(self):
        """Update filled/outline icons and Back button visibility.

        Should be called whenever the current menu changes.
        Reads gui.ui_state.current_menu_id directly.
        """
        if self._seed_dropup is None or self._wallet_dropup is None:
            return  # drop-ups not yet registered — init not complete
        current = self.gui.ui_state.current_menu_id

        # Back button: visible unless we are at the root / home menu
        at_home = current in ("main", None)
        self.buttons["Back"].set_visible(not at_home)

        seed_open = self._seed_dropup.get_state() in (DropUpState.OPENING, DropUpState.OPEN)
        wallet_open = self._wallet_dropup.get_state() in (DropUpState.OPENING, DropUpState.OPEN)

        # Home icon: filled only when on main and no dropup is open
        if current == "main" and not seed_open and not wallet_open:
            self.buttons["Home"].update_icon(BTC_ICONS.HOME)
        else:
            self.buttons["Home"].update_icon(BTC_ICONS.HOME_OUTLINE)

        # Seed icon: filled when dropup open OR when in a seed menu
        if seed_open or current in _SEED_MENUS:
            self.buttons["Seed"].update_icon(BTC_ICONS.KEY)
        else:
            self.buttons["Seed"].update_icon(BTC_ICONS.KEY_OUTLINE)
        #Seed icon: invisible when no seed loaded
        self.buttons["Seed"].set_visible(self.gui.specter_state and len(self.gui.specter_state.loaded_seeds) > 0)

        # Wallet icon: filled when dropup open OR when in a wallet menu
        if wallet_open or current in _WALLET_MENUS:
            self.buttons["Wallet"].update_icon(BTC_ICONS.WALLET)
        else:
            self.buttons["Wallet"].update_icon(BTC_ICONS.WALLET_OUTLINE)
        #Wallet icon: invisible when no seed loaded
        self.buttons["Wallet"].set_visible(self.gui.specter_state and len(self.gui.specter_state.loaded_seeds) > 0)

        # Device icon
        if current in _DEVICE_MENUS and not seed_open and not wallet_open:
            self.buttons["Device"].update_icon(BTC_ICONS.GEAR)
        else:
            self.buttons["Device"].update_icon(BTC_ICONS.GEAR_OUTLINE)

    # ── Button callbacks ──────────────────────────────────────────────────────

    def _dropup_button_cb(self, own_dropup, other_dropup, own_menus, root_menu):
        """Shared logic for Seed and Wallet nav buttons.

        - Closes ``other_dropup`` first (mutual exclusion).
        - If already inside ``own_menus``: exit context root or jump to it.
        - Otherwise: toggle ``own_dropup`` open/closed.
        """
        self._close_dropup(other_dropup)
        current = self.gui.ui_state.current_menu_id
        if current in own_menus:
            if current == root_menu:
                self.on_navigate(None)          # at root → exit context
            else:
                self.gui.jump_to_context_root(root_menu)  # deeper → jump to root
            return
        if own_dropup.get_state() in (DropUpState.OPENING, DropUpState.OPEN):
            self._close_dropup(own_dropup)
        else:
            own_dropup.open()
        self.refresh()


    def _back_cb(self, event=None):
        """Go back one history level, or close any open drop-up first."""
        if self._busy_or_not_init():
            return
        # If a drop-up is open, close it first, then navigate back
        self._close_dropups()
        self.on_navigate(None)

    def _seed_cb(self, event=None):
        """If in seed context root: exit. If in deeper seed menu: jump to root. Otherwise open drop-up."""
        if self._busy_or_not_init():
            return
        self._dropup_button_cb(self._seed_dropup, self._wallet_dropup, _SEED_MENUS, "manage_seedphrase")

    def _home_cb(self, event=None):
        """Navigate to the main/home menu, clearing history."""
        if self._busy_or_not_init():
            return
        # History clearing is handled inside show_menu for target="main"
        self._close_dropups()
        self.gui.on_navigate("main")

    def _wallet_cb(self, event=None):
        """If in wallet context root: exit. If in deeper wallet menu: jump to root. Otherwise open drop-up."""
        if self._busy_or_not_init():
            return
        self._dropup_button_cb(self._wallet_dropup, self._seed_dropup, _WALLET_MENUS, "manage_wallet")

    def _device_cb(self, event=None):
        """If at device root: exit. If in deeper device menu: jump to root. Otherwise enter device."""
        if self._busy_or_not_init():
            return

        current = self.gui.ui_state.current_menu_id
        was_dropup_open = (
            self._seed_dropup.get_state() in (DropUpState.OPENING, DropUpState.OPEN)
            or self._wallet_dropup.get_state() in (DropUpState.OPENING, DropUpState.OPEN)
        )

        #always close drop ups if they are open
        self._close_dropups()
        
        if current not in _DEVICE_MENUS:
            self.gui.show_menu("manage_settings")  # enter device
        elif not was_dropup_open: #pressing button in device menu with open dropup shall just close the dropup
            if current == "manage_settings":
                self.on_navigate(None)                           # at root → exit
            else:
                self.gui.jump_to_context_root("manage_settings")  # deeper → jump to root

        self.refresh()
