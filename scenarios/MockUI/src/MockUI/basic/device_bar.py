"""Device / Navigation Bar — bottom bar of the TopSelector layout.

Layout (left-to-right, full width, STATUS_BAR_PCT% height):
    ┌──────────────────────────────────────────────────────┐
    │ [Back?]        [Home (centred)]   [Battery?] [Gear]  │
    └──────────────────────────────────────────────────────┘

Left  : Back button (only when navigation history exists)
Centre: Home button (always, pinned to centre)
Right : Battery widget (when device has battery) + Settings button
"""

import lvgl as lv
from ..stubs import Battery
from .ui_consts import STATUS_BTN_HEIGHT, STATUS_BTN_WIDTH
from .symbol_lib import BTC_ICONS
from .widgets.btn import Btn


class DeviceBar(lv.obj):
    """Device / navigation bar — bottom of screen."""

    def __init__(self, gui, height_pct=8):
        super().__init__(gui)

        self.gui = gui

        self.set_width(lv.pct(100))
        self.set_height(lv.pct(height_pct))
        # No flex — children are positioned absolutely so home stays centred
        # regardless of whether the back button is present.
        self.set_style_pad_all(0, 0)
        self.set_style_radius(0, 0)
        self.set_style_border_width(0, 0)
        self.set_scroll_dir(lv.DIR.NONE)

        # ── CENTRE: Home (always present, pinned to centre) ──────────────────
        self.home_btn = Btn(
            self,
            icon=BTC_ICONS.HOME_OUTLINE,
            size=(STATUS_BTN_WIDTH, STATUS_BTN_HEIGHT),
            callback=self._home_cb,
        ).make_transparent()
        self.home_btn.align(lv.ALIGN.CENTER, 0, 0)

        # ── RIGHT: Settings (far right) then Battery to its left ─────────────
        self.settings_btn = Btn(
            self,
            icon=BTC_ICONS.GEAR_OUTLINE,
            size=(STATUS_BTN_WIDTH, STATUS_BTN_HEIGHT),
            callback=self._settings_cb,
        ).make_transparent()
        self.settings_btn.align(lv.ALIGN.RIGHT_MID, 0, 0)

        self.batt_icon = Battery(self)
        self.batt_icon.VALUE = gui.specter_state.battery_pct
        self.batt_icon.update()
        self.batt_icon.align_to(self.settings_btn, lv.ALIGN.OUT_LEFT_MID, -4, 0)

        # ── LEFT: Back button (dynamic, only when history exists) ────────────
        self.back_btn = None
        self._rebuild_back_btn()

    # ── Button callbacks ─────────────────────────────────────────────────────

    def _home_cb(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            self.gui.ui_state.clear_history()
            self.gui.show_menu(None)

    def _back_cb(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            self.gui.show_menu(None)  # pop one level

    # All device/settings menus (main + sub-menus)
    _SETTINGS_MENUS = frozenset([
        "manage_settings", "manage_security_settings", "manage_backups",
        "manage_firmware", "interfaces", "manage_storage", "select_language",
        "manage_preferences", "manage_security_features",
    ])

    def _settings_cb(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        current = self.gui.ui_state.current_menu_id
        if current == "manage_settings":
            # Already on main settings — close it (go back to whatever was before)
            self.gui.show_menu(None)
        elif current in self._SETTINGS_MENUS:
            # In a settings sub-menu — pop history entries until manage_settings
            # sits on top of the stack, then let show_menu(None) pop and display it.
            while (self.gui.ui_state.history
                   and self.gui.ui_state.history[-1] != "manage_settings"):
                self.gui.ui_state.pop_menu()
            self.gui.show_menu(None)
        else:
            # Not in settings at all — open main settings
            self.gui.show_menu("manage_settings")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _rebuild_back_btn(self):
        """Create/destroy the back button depending on navigation history."""
        has_history = (
            self.gui.ui_state is not None
            and self.gui.ui_state.history
            and len(self.gui.ui_state.history) > 0
        )
        if has_history and self.back_btn is None:
            self.back_btn = Btn(
                self,
                icon=BTC_ICONS.CARET_LEFT,
                size=(STATUS_BTN_WIDTH, STATUS_BTN_HEIGHT),
                callback=self._back_cb,
            ).make_transparent()
            self.back_btn.align(lv.ALIGN.LEFT_MID, 0, 0)
        elif not has_history and self.back_btn is not None:
            self.back_btn.delete()
            self.back_btn = None

    # ── Refresh ──────────────────────────────────────────────────────────────

    def refresh(self, state):
        """Update dynamic elements from current SpecterState."""
        # Battery: hide by making fully transparent when device has no battery
        if state.has_battery:
            self.batt_icon.CHARGING = state.is_charging
            self.batt_icon.VALUE = state.battery_pct
            self.batt_icon.update()
            self.batt_icon.set_style_opa(lv.OPA.COVER, 0)
        else:
            self.batt_icon.set_style_opa(lv.OPA.TRANSP, 0)

        # Back button visibility
        self._rebuild_back_btn()

        # Home / Settings icon: filled when that menu is active, outline otherwise
        current = self.gui.ui_state.current_menu_id if self.gui.ui_state else None
        home_active = current in ("main", "start_intro_tour", None)
        self.home_btn.update_icon(
            BTC_ICONS.HOME if home_active else BTC_ICONS.HOME_OUTLINE
        )
        settings_active = current in self._SETTINGS_MENUS
        self.settings_btn.update_icon(
            BTC_ICONS.GEAR if settings_active else BTC_ICONS.GEAR_OUTLINE
        )

