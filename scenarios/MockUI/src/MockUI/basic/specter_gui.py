import lvgl as lv

from ..stubs import UIState, SpecterState
from .device_bar import DeviceBar
from .select_and_manage_bar import SelectAndManageSeedsBar, SelectAndManageWalletsBar
from .action_screen import ActionScreen
from .main_menu import MainMenu
from .locked_menu import LockedMenu
from .ui_consts import STATUS_BAR_PCT, SELECT_BAR_PCT, CONTENT_PCT, SCREEN_HEIGHT, SCREEN_WIDTH
from ..wallet import (
    WalletMenu,
    ConnectWalletsMenu,
    SwitchAddSeedsMenu,
    SwitchAddWalletsMenu,
    AddSeedMenu,
    AddWalletMenu,
    SeedPhraseMenu,
    StoreSeedphraseMenu,
    ClearSeedphraseMenu,
    GenerateSeedMenu,
    PassphraseMenu,
    ManageSeedsAndWalletsMenu,
    CreateCustomWalletMenu,
    ViewSignersScreen,
)
from ..device import (
    SecuritySettingsMenu,
    BackupsMenu,
    FirmwareMenu,
    InterfacesMenu,
    StorageMenu,
    SecurityFeaturesMenu,
    LanguageMenu,
    SettingsMenu,
    PreferencesMenu,
)
from ..i18n import I18nManager
from ..tour import GuidedTour
from .keyboard_manager import KeyboardManager

# ── Animation helpers ───────────────────────────────────────────────────────

ANIM_MS = 200  # slide duration in milliseconds

# ── Context sets ─────────────────────────────────────────────────────────────
# DEVICE context: both bars hidden
_CTX_DEVICE = frozenset([
    "manage_settings", "manage_security_settings", "manage_backups",
    "manage_firmware", "interfaces", "manage_storage", "select_language",
    "manage_preferences", "manage_security_features",
    "add_seed", "generate_seedphrase",
    "change_pin", "set_duress_pin", "set_duress_pin_action",
    "set_exceeded_pin_action", "set_allowed_pin_retries",
    "wipe_device", "self_test",
    "backup_to_sd", "restore_from_sd", "remove_backup_from_sd",
    "update_fw_qr", "update_fw_sd", "update_fw_usb",
    "internal_flash", "sdcard", "smartcard",
    "display_settings", "sound_settings",
])
# SEED context: seeds_bar visible, wallets_bar hidden
_CTX_SEED = frozenset([
    "switch_add_seeds",
    "manage_seedphrase", "store_seedphrase", "clear_seedphrase",
    "set_passphrase", "show_seedphrase",
    "store_to_smartcard", "store_to_sd", "store_to_flash",
    "clear_from_smartcard", "clear_from_sd", "clear_from_flash", "clear_all_storage",
    "import_from_keyboard", "import_from_qr", "import_from_sd",
    "import_from_smartcard", "import_from_flash",
])
# WALLET context: both bars visible (data-permitting)
_CTX_WALLET = frozenset([
    "switch_add_wallets",
    "manage_wallet",
    "manage_wallet_descriptor", "change_network", "view_signers",
    "export_wallet",
    "import_wallet_from_qr", "import_wallet_from_sd",
])
# MAIN (wallet+seed) context: both bars visible (data-permitting)
# Everything not in the above sets falls into this context.


def _context(menu_id, history=None):
    """Return 'device'|'seed'|'wallet'|'main' for a menu ID.

    Unknown IDs inherit from their parent in the navigation history.
    If history is None or empty falls back to 'main'.
    """
    mid = menu_id or "main"
    if mid in _CTX_DEVICE:
        return "device"
    if mid in _CTX_SEED:
        return "seed"
    if mid in _CTX_WALLET:
        return "wallet"
    if mid in ("main", "scan_qr", "view_addresses", "connect_companion_app",
               "start_intro_tour", "locked",
               "add_wallet", "create_custom_wallet",
               "connect_sw_wallet",
               "connect_sparrow", "connect_nunchuck", "connect_bluewallet", "connect_other"):
        return "main"
    # Unknown ID: inherit from parent (last entry in history stack)
    if history:
        for parent in reversed(history):
            if parent and parent != mid:
                return _context(parent, None)  # one level only, no recursion loop
    return "main"


def _transition_params(from_id, to_id, history=None):
    """Return (region, axis, new_from) for a FORWARD navigation.

    region: 'a' | 'b' | 'c' | 'd'
    axis:   'horizontal' | 'vertical'
    new_from: direction the NEW screen enters from
              horizontal: 'right' | 'left'
              vertical:   'top'   (new slides down in from top)

    Returns None if no animation is needed (same effective context+menu).
    """
    fc = _context(from_id, history)
    tc = _context(to_id, history)

    # Same menu — no animation
    if (from_id or "main") == (to_id or "main"):
        return None

    # ── Device ↔ any ─────────────────────────────────────────────────────────
    if tc == "device" and fc != "device":
        return ("c", "horizontal", "right")   # device enters from right
    if fc == "device" and tc != "device":
        return ("c", "horizontal", "left")    # device exits right, new from left

    # ── Cross-context vertical transitions ───────────────────────────────────
    if fc in ("main", "wallet") and tc == "seed":
        # Going UP to seed (less specific): new seed content enters from top
        return ("b", "vertical", "top")
    if fc == "seed" and tc in ("main", "wallet"):
        # Coming DOWN from seed back to wallet/main: old lifts off
        # Represented as new_from="bottom" meaning old exits upward (new was beneath)
        return ("b", "vertical", "bottom")

    if fc == "main" and tc == "wallet":
        # Going UP to wallet (more specific within seed+wallet space)
        return ("a", "vertical", "top")
    if fc == "wallet" and tc == "main":
        return ("a", "vertical", "bottom")

    # ── Within same context: horizontal ──────────────────────────────────────
    return (_context_region(tc), "horizontal", "right")


def _context_region(ctx):
    """Return the content region for within-context navigation."""
    # Within any context the full content area of that context moves
    if ctx == "device":
        return "c"  # no bars visible; full space below device_bar
    if ctx == "seed":
        return "b"  # below seeds_bar (wallets_bar hidden)
    if ctx == "wallet":
        return "a"  # below wallets_bar
    return "a"      # main: below wallets_bar (or seeds_bar if wallets hidden)


def _invert_params(region, axis, new_from):
    """Invert transition params for back navigation."""
    inv = {"right": "left", "left": "right", "top": "bottom", "bottom": "top"}
    return (region, axis, inv[new_from])


class SpecterGui(lv.obj):
    # Static tour step definitions: (element_spec, i18n_key, position)
    # element_spec is None, a dotted attribute-path string, or a (x, y, w, h) tuple.
    # Resolved to runtime objects by GuidedTour.resolve_steps() before use.
    INTRO_TOUR_STEPS = [
        (None,                              "TOUR_INTRO",        "center"),
        ("device_bar.home_btn",             "TOUR_HOME",         "below"),
        ("device_bar.settings_btn",         "TOUR_SETTINGS",     "below"),
        ("device_bar.batt_icon",            "TOUR_BATTERY",      "below"),
        ("seeds_bar",                       "TOUR_SEEDS_BAR",    "below"),
        ("wallets_bar",                     "TOUR_WALLETS_BAR",  "below"),
        ((435, 143, 28, 28),                "TOUR_HELP_ICON",    "left"),
    ]

    def __init__(self, specter_state=None, ui_state=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_scroll_dir(lv.DIR.NONE)

        self.on_navigate = self.show_menu
        
        # Initialize i18n manager
        self.i18n = I18nManager()

        if specter_state:
            self.specter_state = specter_state
        else:
            self.specter_state = SpecterState()

        # optional UIState instance used to track menu history
        if ui_state:
            self.ui_state = ui_state
        else:
            self.ui_state = UIState()

        self.current_screen = None
        self.keyboard_manager = KeyboardManager(self)
        self._animating = False      # True while a slide animation is running
        self._anim_refs = None       # keeps Python callbacks alive during animation
        self._seeds_bar_visible = False   # tracked after each refresh_ui
        self._wallets_bar_visible = False

        # Allow seeds_bar / wallets_bar to render outside our bounds during
        # bar slide animations.  Set once here — never toggled — so device_bar
        # layout is never disturbed.
        self.add_flag(lv.obj.FLAG.OVERFLOW_VISIBLE)

        # ── Bar layout ────────────────────────────────────────────────────────
        # Top: Seeds select-and-manage bar (SELECT_BAR_PCT%)
        self.seeds_bar = SelectAndManageSeedsBar(self, height_pct=SELECT_BAR_PCT)
        self.seeds_bar.align(lv.ALIGN.TOP_MID, 0, 0)

        # Below seeds: Wallets select-and-manage bar (SELECT_BAR_PCT%)
        self.wallets_bar = SelectAndManageWalletsBar(self, height_pct=SELECT_BAR_PCT)
        self.wallets_bar.align_to(self.seeds_bar, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)

        # Bottom: Device / navigation bar (STATUS_BAR_PCT%) — always visible
        self.device_bar = DeviceBar(self, height_pct=STATUS_BAR_PCT)
        self.device_bar.align(lv.ALIGN.BOTTOM_MID, 0, 0)

        # Content area between top bars and device bar (positioned by refresh_ui)
        self.content = lv.obj(self)
        self.content.set_width(lv.pct(100))
        self.content.set_height(lv.pct(CONTENT_PCT))  # overridden by refresh_ui
        self.content.set_layout(lv.LAYOUT.FLEX)
        self.content.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.content.set_style_pad_all(0, 0)
        self.content.set_style_radius(0, 0)
        self.content.set_style_border_width(0, 0)
        self.content.set_scroll_dir(lv.DIR.NONE)

        # initially show the main menu
        self.show_menu(None)
        
        # Start guided tour on first startup (after UI is fully constructed)
        if self.ui_state.run_tour_on_startup:
            GuidedTour(self, GuidedTour.resolve_steps(self.INTRO_TOUR_STEPS, self)).start()

        # periodic refresh of both bars every 30 seconds
        def _tick(timer):
            self.refresh_ui()

        lv.timer_create(_tick, 30_000, None)

    def change_language(self, lang_code):
        """
        Change the active language.
        
        Args:
            lang_code: ISO 639-1 language code (e.g., 'en', 'de')
        """
        # Switch language in i18n manager
        self.i18n.set_language(lang_code)

    # ── Menu categories for bar visibility ──────────────────────────────────
    # Reuse module-level context sets; keep class attrs for backward compat.
    _DEVICE_MENUS = _CTX_DEVICE
    _SEED_MENUS = _CTX_SEED

    def refresh_ui(self):
        """Refresh all bars, bar visibility, layout, and current screen content."""
        state = self.specter_state
        current = self.ui_state.current_menu_id if self.ui_state else None

        self.device_bar.refresh(state)
        self.seeds_bar.refresh(state)
        self.wallets_bar.refresh(state)

        # ── Bar visibility rules ──────────────────────────────────────────────
        seed_loaded = state.active_seed is not None
        has_extra_wallet = any(
            not w.is_default_wallet() for w in state.registered_wallets
        )

        seeds_visible = (seed_loaded
                         and current not in self._DEVICE_MENUS)
        wallets_visible = (seed_loaded
                           and has_extra_wallet
                           and current not in self._DEVICE_MENUS
                           and current not in self._SEED_MENUS)

        self._seeds_bar_visible = seeds_visible
        self._wallets_bar_visible = wallets_visible
        self.seeds_bar.set_style_opa(lv.OPA.COVER if seeds_visible else lv.OPA.TRANSP, 0)
        self.wallets_bar.set_style_opa(lv.OPA.COVER if wallets_visible else lv.OPA.TRANSP, 0)

        # Reposition and resize content between visible top bars and device bar
        device_h = SCREEN_HEIGHT * STATUS_BAR_PCT // 100
        select_h = SCREEN_HEIGHT * SELECT_BAR_PCT // 100
        content_y = 0
        if seeds_visible:
            content_y += select_h
        if wallets_visible:
            content_y += select_h
        self.content.set_height(SCREEN_HEIGHT - device_h - content_y)
        self.content.align(lv.ALIGN.TOP_MID, 0, content_y)

        # ── Rebuild current screen so its content reflects latest state ───────
        # Skip screen rebuild if the keyboard is open — destroying the screen
        # mid-input would discard the user's text and re-run __init__ (which
        # generates a new random name, etc.).  Bar/layout updates above still
        # apply; the screen will be rebuilt on the next refresh after the
        # keyboard closes.
        if self.keyboard_manager.textarea is not None:
            return
        if self._animating:
            return  # don't rebuild mid-transition; _do_transition drives this
        if self.current_screen:
            self.current_screen.delete()
        self._build_screen(current)

    def _build_screen(self, current):
        """Instantiate the correct screen class for *current* menu_id."""
        # If the device is locked, always show the locked screen
        if self.specter_state.is_locked:
            self.ui_state.clear_history()
            self.ui_state.current_menu_id = "locked"
            self.current_screen = LockedMenu(self)
            return

        if current is None:
            current = self.ui_state.current_menu_id

        if current in ("main", "start_intro_tour"):
            self.current_screen = MainMenu(self)
        elif current == "manage_wallet":
            self.current_screen = WalletMenu(self)
        elif current == "view_signers":
            self.current_screen = ViewSignersScreen(self)
        elif current == "manage_security_settings":
            self.current_screen = SecuritySettingsMenu(self)
        elif current == "manage_backups":
            self.current_screen = BackupsMenu(self)
        elif current == "manage_firmware":
            self.current_screen = FirmwareMenu(self)
        elif current == "connect_sw_wallet":
            self.current_screen = ConnectWalletsMenu(self)
        elif current == "add_seed":
            self.current_screen = AddSeedMenu(self)
        elif current == "add_wallet":
            self.current_screen = AddWalletMenu(self)
        elif current == "switch_add_seeds":
            self.current_screen = SwitchAddSeedsMenu(self)
        elif current == "switch_add_wallets":
            self.current_screen = SwitchAddWalletsMenu(self)
        elif current == "manage_security_features":
            self.current_screen = SecurityFeaturesMenu(self)
        elif current == "interfaces":
            self.current_screen = InterfacesMenu(self)
        elif current == "manage_seedphrase":
            self.current_screen = SeedPhraseMenu(self)
        elif current == "store_seedphrase":
            self.current_screen = StoreSeedphraseMenu(self)
        elif current == "clear_seedphrase":
            self.current_screen = ClearSeedphraseMenu(self)
        elif current == "generate_seedphrase":
            self.current_screen = GenerateSeedMenu(self)
        elif current == "set_passphrase":
            self.current_screen = PassphraseMenu(self)
        elif current == "manage_seed_wallet":
            self.current_screen = ManageSeedsAndWalletsMenu(self)
        elif current == "create_custom_wallet":
            self.current_screen = CreateCustomWalletMenu(self)
        elif current == "manage_storage":
            self.current_screen = StorageMenu(self)
        elif current == "select_language":
            self.current_screen = LanguageMenu(self)
        elif current == "manage_preferences":
            self.current_screen = PreferencesMenu(self)
        elif current == "manage_settings":
            self.current_screen = SettingsMenu(self)
        else:
            # For all other actions, show a generic action screen
            title = current.replace("_", " ")
            title = title[0].upper() + title[1:] if title else ""
            self.current_screen = ActionScreen(title, self)

    def show_menu(self, target_menu_id=None):
        old_id = self.ui_state.current_menu_id if self.ui_state else None
        going_back = target_menu_id is None

        # Update UIState navigation history (before building screen)
        if going_back:
            self.ui_state.pop_menu()
        elif target_menu_id == "start_intro_tour":
            self.ui_state.clear_history()
            self.ui_state.current_menu_id = target_menu_id
        else:
            self.ui_state.push_menu(target_menu_id)

        new_id = self.ui_state.current_menu_id if self.ui_state else None
        history = list(self.ui_state.history) if self.ui_state else []

        if going_back:
            # Forward direction would be new→old; invert it for back
            fwd = _transition_params(new_id, old_id, history)
            params = _invert_params(*fwd) if fwd is not None else None
        else:
            params = _transition_params(old_id, new_id, history)

        if params is not None and self.current_screen is not None and not self._animating:
            self._do_transition(*params)
        else:
            self.refresh_ui()

        if self.ui_state.current_menu_id == "start_intro_tour":
            self.ui_state.current_menu_id = "main"
            GuidedTour(self, GuidedTour.resolve_steps(self.INTRO_TOUR_STEPS, self)).start()

    def refresh_ui_animated(self, region, axis, new_from):
        """Animate a bar-caret transition with an explicit region/axis/direction.

        Falls back to plain refresh_ui() if an animation is already running
        or there is no existing screen to animate away from.
        """
        if self.current_screen is None or self._animating:
            self.refresh_ui()
            return
        self._do_transition(region, axis, new_from)

    def _do_transition(self, region, axis, new_from):
        """Animate from the current screen to a freshly built new screen.

        Parameters
        ----------
        region   : 'a' | 'b' | 'c' | 'd'
                   Which LVGL objects move:
                     a — content only  (below wallets_bar / seeds_bar)
                     b — wallets_bar + content
                     c — seeds_bar + wallets_bar + content
                     d — seeds_bar only  (seed-bar caret, wallet fits)
        axis     : 'horizontal' | 'vertical'
        new_from : direction the NEW screen enters from
                   horizontal: 'right' | 'left'
                   vertical:   'top'   → new slides DOWN over old (old stays)
                               'bottom'→ old exits UP revealing new beneath

        device_bar is NEVER animated.
        """
        old_screen = self.current_screen
        if old_screen is None:
            self.refresh_ui()
            return

        select_h = SCREEN_HEIGHT * SELECT_BAR_PCT // 100
        device_h = SCREEN_HEIGHT * STATUS_BAR_PCT // 100

        # Capture bar visibility BEFORE refresh_ui changes it
        seeds_was = self._seeds_bar_visible
        wallets_was = self._wallets_bar_visible

        # Content geometry BEFORE the transition
        cy_before = (select_h if seeds_was else 0) + (select_h if wallets_was else 0)
        ch_before = SCREEN_HEIGHT - device_h - cy_before

        # ── Region 'd': only seeds_bar slides; rebuild content in-place ───────
        if region == "d":
            W = SCREEN_WIDTH
            nx = W if new_from == "right" else -W

            # Refresh state in-place (bar label + content update without animation)
            self.refresh_ui()
            # After refresh_ui seeds_bar is at x=0; push it to the off-screen
            # start position then animate it in.
            self.seeds_bar.set_x(nx)

            self._animating = True
            refs = []

            cb_s_in = lambda anim, v: self.seeds_bar.set_x(v)
            a_s_in = lv.anim_t(); a_s_in.init()
            a_s_in.set_custom_exec_cb(cb_s_in)
            a_s_in.set_values(nx, 0)
            a_s_in.set_duration(ANIM_MS)
            a_s_in.start()
            refs.extend([cb_s_in, a_s_in])

            gui = self
            def _on_done_d(timer):
                timer.delete()
                gui._animating = False
                gui._anim_refs = None
                gui.seeds_bar.set_x(0)

            t = lv.timer_create(_on_done_d, ANIM_MS + 50, None)
            refs.extend([_on_done_d, t])
            self._anim_refs = refs
            return

        # ── Build new screen (with flex disabled so old_screen isn't deleted) ─
        self.content.set_layout(lv.LAYOUT.NONE)
        self.current_screen = None
        self.refresh_ui()
        new_screen = self.current_screen

        if new_screen is None:
            # Nothing to show; abort gracefully
            self.current_screen = old_screen
            self.content.align(lv.ALIGN.TOP_MID, 0, cy_before)
            self.content.set_height(ch_before)
            self.content.set_layout(lv.LAYOUT.FLEX)
            self.content.set_flex_flow(lv.FLEX_FLOW.COLUMN)
            return

        # Content geometry AFTER the transition (set by refresh_ui above)
        seeds_now = self._seeds_bar_visible
        wallets_now = self._wallets_bar_visible
        cy_after = (select_h if seeds_now else 0) + (select_h if wallets_now else 0)
        ch_after = SCREEN_HEIGHT - device_h - cy_after

        # Expand content to cover the entire area below device_bar (y=0),
        # make its background transparent, and position each screen at its
        # correct absolute y inside content.  This avoids OVERFLOW_VISIBLE
        # tricks and means bars (siblings of content) are always drawn over
        # a transparent gap — no black rectangle.
        anim_total_h = SCREEN_HEIGHT - device_h
        self.content.align(lv.ALIGN.TOP_MID, 0, 0)
        self.content.set_height(anim_total_h)
        self.content.set_style_bg_opa(lv.OPA.TRANSP, 0)

        # Place screens at their visual y positions within content
        old_screen.set_y(cy_before)
        new_screen.set_y(cy_after)
        old_screen.set_size(SCREEN_WIDTH, ch_before)
        new_screen.set_size(SCREEN_WIDTH, ch_after)

        # Bars are siblings of content; they keep their absolute positions.
        # Move them to front so they paint over content's transparent area.
        self.seeds_bar.move_foreground()
        self.wallets_bar.move_foreground()

        self._animating = True

        W = SCREEN_WIDTH
        refs = []

        # ── Horizontal transition ─────────────────────────────────────────────
        if axis == "horizontal":
            nx = W if new_from == "right" else -W
            ox = -W if new_from == "right" else W

            new_screen.set_x(nx)  # old_screen.x stays 0

            cb_new = lambda anim, v: new_screen.set_x(v)
            cb_old = lambda anim, v: old_screen.set_x(v)
            for cb, vs, ve in [(cb_new, nx, 0), (cb_old, 0, ox)]:
                a = lv.anim_t(); a.init()
                a.set_custom_exec_cb(cb); a.set_values(vs, ve)
                a.set_duration(ANIM_MS); a.start()
                refs.extend([cb, a])

            # Bars in the animated region slide in/out with the content.
            # "In the region": region 'c' → seeds+wallets; 'b' → wallets; 'a' → none.
            bars_in_region = []
            if region in ("b", "c"):
                bars_in_region.append(self.wallets_bar)
            if region == "c":
                bars_in_region.append(self.seeds_bar)

            for bar, was_v, now_v in [
                (self.seeds_bar, seeds_was, seeds_now),
                (self.wallets_bar, wallets_was, wallets_now),
            ]:
                if bar not in bars_in_region:
                    continue
                if was_v and now_v:
                    # Stays visible: slides out with old, new slides in from nx
                    bar.set_x(nx)
                    cb = lambda anim, v, b=bar: b.set_x(v)
                    a = lv.anim_t(); a.init()
                    a.set_custom_exec_cb(cb); a.set_values(nx, 0)
                    a.set_duration(ANIM_MS); a.start()
                    refs.extend([cb, a])
                elif was_v and not now_v:
                    # Exits with old content
                    bar.set_style_opa(lv.OPA.COVER, 0)
                    bar.set_x(0)
                    cb = lambda anim, v, b=bar: b.set_x(v)
                    a = lv.anim_t(); a.init()
                    a.set_custom_exec_cb(cb); a.set_values(0, ox)
                    a.set_duration(ANIM_MS); a.start()
                    refs.extend([cb, a])
                elif not was_v and now_v:
                    # Enters with new content
                    bar.set_x(nx)
                    cb = lambda anim, v, b=bar: b.set_x(v)
                    a = lv.anim_t(); a.init()
                    a.set_custom_exec_cb(cb); a.set_values(nx, 0)
                    a.set_duration(ANIM_MS); a.start()
                    refs.extend([cb, a])

        # ── Vertical transition ───────────────────────────────────────────────
        else:
            # Bars that move with the animated region
            # region 'b' → wallets_bar; region 'c' → seeds_bar + wallets_bar
            bars_in_region = []
            if region in ("b", "c") and wallets_was:
                bars_in_region.append(self.wallets_bar)
            if region == "c" and seeds_was:
                bars_in_region.append(self.seeds_bar)

            # Animated height = content height of the OLD context
            anim_h = ch_before
            # Screens may need to render outside content bounds (above it);
            # OVERFLOW_VISIBLE is safe here since content is transparent
            # and bars are in front.
            self.content.add_flag(lv.obj.FLAG.OVERFLOW_VISIBLE)

            if new_from == "top":
                # New slides DOWN over old (old stays, new enters from above)
                # new_screen starts above its final position by anim_h
                new_screen.set_y(cy_after - anim_h)

                cb_new = lambda anim, v: new_screen.set_y(v)
                a_new = lv.anim_t(); a_new.init()
                a_new.set_custom_exec_cb(cb_new)
                a_new.set_values(cy_after - anim_h, cy_after)
                a_new.set_duration(ANIM_MS); a_new.start()
                refs.extend([cb_new, a_new])

                # Bars in region slide down from above
                for b in bars_in_region:
                    orig_y = b.get_y()
                    b.set_y(orig_y - anim_h)
                    cb_b = lambda anim, v, bw=b: bw.set_y(v)
                    a_b = lv.anim_t(); a_b.init()
                    a_b.set_custom_exec_cb(cb_b)
                    a_b.set_values(orig_y - anim_h, orig_y)
                    a_b.set_duration(ANIM_MS); a_b.start()
                    refs.extend([cb_b, a_b])

            else:  # new_from == "bottom"
                # Old exits UPWARD revealing stationary new beneath.
                # new_screen is already at y=cy_after (correct final position).
                # old_screen is at y=cy_before.
                # old_screen must be on top so it covers new_screen until it lifts.
                old_screen.move_foreground()

                cb_old = lambda anim, v: old_screen.set_y(v)
                a_old = lv.anim_t(); a_old.init()
                a_old.set_custom_exec_cb(cb_old)
                a_old.set_values(cy_before, cy_before - anim_h)
                a_old.set_duration(ANIM_MS); a_old.start()
                refs.extend([cb_old, a_old])

                # Bars in region also exit upward
                for b in bars_in_region:
                    orig_y = b.get_y()
                    cb_b = lambda anim, v, bw=b: bw.set_y(v)
                    a_b = lv.anim_t(); a_b.init()
                    a_b.set_custom_exec_cb(cb_b)
                    a_b.set_values(orig_y, orig_y - anim_h)
                    a_b.set_duration(ANIM_MS); a_b.start()
                    refs.extend([cb_b, a_b])

        # ── Cleanup timer ─────────────────────────────────────────────────────
        old_s = old_screen
        new_s = new_screen
        content = self.content
        gui = self
        s_was, s_now = seeds_was, seeds_now
        w_was, w_now = wallets_was, wallets_now

        def _on_done(timer):
            timer.delete()
            gui._animating = False
            gui._anim_refs = None
            # Restore bar positions and opacity
            content.remove_flag(lv.obj.FLAG.OVERFLOW_VISIBLE)
            gui.seeds_bar.set_pos(0, 0)
            gui.wallets_bar.set_pos(0, 0)
            if s_was and not s_now:
                gui.seeds_bar.set_style_opa(lv.OPA.TRANSP, 0)
            if w_was and not w_now:
                gui.wallets_bar.set_style_opa(lv.OPA.TRANSP, 0)
            gui.seeds_bar.align(lv.ALIGN.TOP_MID, 0, 0)
            gui.wallets_bar.align_to(gui.seeds_bar, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)
            # Restore content geometry, opacity, and layout
            content.set_style_bg_opa(lv.OPA.COVER, 0)
            content.align(lv.ALIGN.TOP_MID, 0, cy_after)
            content.set_height(ch_after)
            content.set_layout(lv.LAYOUT.FLEX)
            content.set_flex_flow(lv.FLEX_FLOW.COLUMN)
            new_s.set_pos(0, 0)
            content.move_foreground()
            try:
                old_s.delete()
            except Exception:
                pass

        t = lv.timer_create(_on_done, ANIM_MS + 50, None)
        refs.extend([_on_done, t])
        self._anim_refs = refs
