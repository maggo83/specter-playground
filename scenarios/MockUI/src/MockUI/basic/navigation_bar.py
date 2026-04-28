"""NavigationBar — permanent bottom navigation bar for Specter MockUI.

Layout (left-to-right, full width, STATUS_BAR_PCT% height):
    ┌───────────────────────────────────────────────────────────────┐
    │  [Back]   [Seed]   [Home]   [Wallet]   [Device]              │
    │  pos 1    pos 2    pos 3    pos 4      pos 5                  │
    └───────────────────────────────────────────────────────────────┘

All five slots have fixed positions (SCREEN_WIDTH / 5 = 96 px each).
When the Back button is hidden, the other buttons stay in their slots —
they do NOT redistribute.

Filled vs outline icon rules
─────────────────────────────
- Home   → filled when current_menu_id == "main"
- Seed   → filled when current_menu_id is in _SEED_MENUS
- Wallet → filled when current_menu_id is in _WALLET_MENUS
- Device → filled when current_menu_id is in _DEVICE_MENUS
- Back   → always filled (CARET_LEFT, no outline variant)

Drop-up wiring
──────────────
Call set_seed_dropup(obj) / set_wallet_dropup(obj) after construction to
register overlay panels.  Tapping Seed / Wallet toggles the drop-up via
obj.toggle().  Until a drop-up is registered, tapping navigates to the
switch_add_seeds / switch_add_wallets fallback menu instead.
"""

import lvgl as lv
from .ui_consts import (
    SCREEN_WIDTH, STATUS_BTN_HEIGHT, STATUS_BTN_WIDTH,
)
from .symbol_lib import BTC_ICONS
from .widgets.btn import Btn

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

# ── Slot geometry ─────────────────────────────────────────────────────────────
_SLOT_W = SCREEN_WIDTH // 5   # 96 px per slot


class NavigationBar(lv.obj):
    """Permanent bottom navigation bar with 5 fixed-position icon buttons."""

    def __init__(self, gui, height_pct=8):
        super().__init__(gui)

        self.gui = gui

        # Optional drop-up panel references (set via set_*_dropup after init)
        self._seed_dropup = None
        self._wallet_dropup = None

        # ── Bar container style ───────────────────────────────────────────────
        self.set_width(lv.pct(100))
        self.set_height(lv.pct(height_pct))
        self.set_layout(lv.LAYOUT.NONE)   # absolute child positioning
        self.set_style_pad_all(0, 0)
        self.set_style_radius(0, 0)
        self.set_style_border_width(0, 0)
        self.set_scroll_dir(lv.DIR.NONE)

        h = STATUS_BTN_HEIGHT

        # ── Slot 1: Back ──────────────────────────────────────────────────────
        self.back_btn = Btn(
            self,
            icon=BTC_ICONS.CARET_LEFT,
            size=(_SLOT_W, h),
            callback=self._back_cb,
        )
        self.back_btn.make_transparent()
        self.back_btn.align(lv.ALIGN.LEFT_MID, 0 * _SLOT_W, 0)

        # ── Slot 2: Seed ──────────────────────────────────────────────────────
        self.seed_btn = Btn(
            self,
            icon=BTC_ICONS.KEY_OUTLINE,
            size=(_SLOT_W, h),
            callback=self._seed_cb,
        )
        self.seed_btn.make_transparent()
        self.seed_btn.align(lv.ALIGN.LEFT_MID, 1 * _SLOT_W, 0)

        # ── Slot 3: Home ──────────────────────────────────────────────────────
        self.home_btn = Btn(
            self,
            icon=BTC_ICONS.HOME_OUTLINE,
            size=(_SLOT_W, h),
            callback=self._home_cb,
        )
        self.home_btn.make_transparent()
        self.home_btn.align(lv.ALIGN.LEFT_MID, 2 * _SLOT_W, 0)

        # ── Slot 4: Wallet ────────────────────────────────────────────────────
        self.wallet_btn = Btn(
            self,
            icon=BTC_ICONS.WALLET_OUTLINE,
            size=(_SLOT_W, h),
            callback=self._wallet_cb,
        )
        self.wallet_btn.make_transparent()
        self.wallet_btn.align(lv.ALIGN.LEFT_MID, 3 * _SLOT_W, 0)

        # ── Slot 5: Device ────────────────────────────────────────────────────
        self.device_btn = Btn(
            self,
            icon=BTC_ICONS.GEAR_OUTLINE,
            size=(_SLOT_W, h),
            callback=self._device_cb,
        )
        self.device_btn.make_transparent()
        self.device_btn.align(lv.ALIGN.LEFT_MID, 4 * _SLOT_W, 0)

    # ── Drop-up wiring ────────────────────────────────────────────────────────

    def set_seed_dropup(self, dropup):
        """Register the seed drop-up overlay panel."""
        self._seed_dropup = dropup

    def set_wallet_dropup(self, dropup):
        """Register the wallet drop-up overlay panel."""
        self._wallet_dropup = dropup

    # ── Public API ────────────────────────────────────────────────────────────

    def refresh(self):
        """Update filled/outline icons and Back button visibility.

        Should be called whenever the current menu changes.
        Reads gui.ui_state.current_menu_id directly.
        """
        current = self.gui.ui_state.current_menu_id

        # Back button: visible unless we are at the root / home menu
        at_home = current in ("main", "locked", None)
        self.back_btn.set_visible(not at_home)

        # Home icon: filled only when on main and no dropup is open
        seed_open = self._seed_dropup is not None and self._seed_dropup.is_open()
        wallet_open = self._wallet_dropup is not None and self._wallet_dropup.is_open()
        if current == "main" and not seed_open and not wallet_open:
            self.home_btn.update_icon(BTC_ICONS.HOME)
        else:
            self.home_btn.update_icon(BTC_ICONS.HOME_OUTLINE)

        # Seed icon: filled when dropup open OR when in a seed menu
        if seed_open or current in _SEED_MENUS:
            self.seed_btn.update_icon(BTC_ICONS.KEY)
        else:
            self.seed_btn.update_icon(BTC_ICONS.KEY_OUTLINE)
        #Seed icon: invisible when no seed loaded
        self.seed_btn.set_visible(self.gui.specter_state and len(self.gui.specter_state.loaded_seeds) > 0)

        # Wallet icon: filled when dropup open OR when in a wallet menu
        if wallet_open or current in _WALLET_MENUS:
            self.wallet_btn.update_icon(BTC_ICONS.WALLET)
        else:
            self.wallet_btn.update_icon(BTC_ICONS.WALLET_OUTLINE)
        #Wallet icon: invisible when no seed loaded
        self.wallet_btn.set_visible(self.gui.specter_state and len(self.gui.specter_state.loaded_seeds) > 0)

        # Device icon
        if current in _DEVICE_MENUS:
            self.device_btn.update_icon(BTC_ICONS.GEAR)
        else:
            self.device_btn.update_icon(BTC_ICONS.GEAR_OUTLINE)

    # ── Button callbacks ──────────────────────────────────────────────────────

    def _back_cb(self, event=None):
        """Go back one history level, or close any open drop-up first."""
        # If a drop-up is open, close it instead of navigating back
        if self._seed_dropup is not None and self._seed_dropup.is_open():
            self._seed_dropup.close()
            return
        if self._wallet_dropup is not None and self._wallet_dropup.is_open():
            self._wallet_dropup.close()
            return
        self.gui.show_menu(None)

    def _seed_cb(self, event=None):
        """Toggle the seed drop-up, close if already in a seed menu, or open the add/switch screen."""
        # Always close the wallet dropup first (mutual exclusion)
        if self._wallet_dropup is not None and self._wallet_dropup.is_open():
            self._wallet_dropup.close()
        if self._seed_dropup is not None:
            if self._seed_dropup.is_open():
                self._seed_dropup.close()
            elif self.gui.ui_state.current_menu_id in _SEED_MENUS:
                # Already in a seed menu → navigate back
                self.gui.show_menu(None)
                return
            else:
                self._seed_dropup.open()
        else:
            if self.gui.ui_state.current_menu_id in _SEED_MENUS:
                self.gui.show_menu(None)
                return
            else:
                self.gui.show_menu("switch_add_seeds")
                return
        self.refresh()

    def _home_cb(self, event=None):
        """Navigate to the main/home menu, clearing history."""
        self.gui.ui_state.clear_history()
        self.gui.show_menu("main")

    def _wallet_cb(self, event=None):
        """Toggle the wallet drop-up, close if already in a wallet menu, or open the add/switch screen."""
        # Always close the seed dropup first (mutual exclusion)
        if self._seed_dropup is not None and self._seed_dropup.is_open():
            self._seed_dropup.close()
        if self._wallet_dropup is not None:
            if self._wallet_dropup.is_open():
                self._wallet_dropup.close()
            elif self.gui.ui_state.current_menu_id in _WALLET_MENUS:
                # Already in a wallet menu → navigate back
                self.gui.show_menu(None)
                return
            else:
                self._wallet_dropup.open()
        else:
            if self.gui.ui_state.current_menu_id in _WALLET_MENUS:
                self.gui.show_menu(None)
                return
            else:
                self.gui.show_menu("switch_add_wallets")
                return
        self.refresh()

    def _device_cb(self, event=None):
        """"If in device submenu: go back to device menu. If in device menu: go back (same as back button), otherwise navigate to manage settings."""
        if self.gui.ui_state.current_menu_id == "manage_settings":
            self.gui.show_menu(None)
        elif self.gui.ui_state.current_menu_id in _DEVICE_MENUS:
            while self.gui.ui_state.current_menu_id not in ("manage_settings", "main_menu"):
                self.gui.ui_state.pop_menu()
            if self.gui.ui_state.current_menu_id == "manage_settings":
                self.gui.ui_state.pop_menu()
            self.gui.show_menu("manage_settings")
        else:
            self.gui.show_menu("manage_settings")
