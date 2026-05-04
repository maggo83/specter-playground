import lvgl as lv

from ..stubs import UIState, SpecterState
from .device_bar import DeviceBar
from .wallet_bar import WalletBar
from .navigation_bar import NavigationBar
from .dropup import SeedDropUp, WalletDropUp
from .action_screen import ActionScreen
from .main_menu import MainMenu
from .locked_menu import LockedMenu
from .ui_consts import STATUS_BAR_PCT, CONTENT_PCT, SCREEN_WIDTH, SCREEN_HEIGHT

# ── Animation constants ───────────────────────────────────────────────────────
ANIM_MS          = 150   # horizontal slide duration (ms)
ANIM_MS_VERTICAL = 300   # vertical slide duration (ms)

# ── Context sets ─────────────────────────────────────────────────────────────
# _CTX_*: only the direct nav-bar entry points (for to_ctx_root detection).
# _ALL_*: every known menu in that context (for reliable _context() lookup
#         without depending on history, needed for jump_to_context_root).
_CTX_DEVICE    = frozenset(["manage_settings"])
_CTX_SEED      = frozenset(["manage_seedphrase", "switch_add_seeds", "add_seed"])
_CTX_WALLET    = frozenset(["manage_wallet",     "switch_add_wallets", "add_wallet"])
_ALL_CTX_ROOTS = _CTX_DEVICE | _CTX_SEED | _CTX_WALLET

_ALL_DEVICE = frozenset([
    "manage_settings", "manage_security_settings", "manage_security_features",
    "manage_backups", "manage_firmware", "interfaces", "manage_storage",
    "manage_preferences", "select_language",
])
_ALL_SEED = frozenset([
    "manage_seedphrase", "switch_add_seeds", "add_seed",
    "store_seedphrase", "clear_seedphrase", "generate_seedphrase",
    "set_passphrase", "manage_seed_wallet", "related_wallets_for_seed",
])
_ALL_WALLET = frozenset([
    "manage_wallet", "switch_add_wallets", "add_wallet",
    "view_signers", "connect_sw_wallet", "create_custom_wallet",
])


def _context_direct(menu_id):
    """Classify using _ALL_* sets without history.  Used only by jump_to_context_root."""
    mid = menu_id or "main"
    if mid in _ALL_DEVICE:
        return "device"
    if mid in _ALL_SEED:
        return "seed"
    if mid in _ALL_WALLET:
        return "wallet"
    return "main"


def _context(menu_id, history=None):
    """Return 'device'|'seed'|'wallet'|'main' for *menu_id*.

    Only the explicit nav-bar entry points (_CTX_*) are classified directly.
    All other menus inherit from the nearest known-context parent in *history*
    so that the animation matches how the user arrived (e.g. connect_sw_wallet
    from main → main context; from wallet nav button → wallet context).
    Falls back to 'main' when history is empty or all parents are unknown.
    """
    mid = menu_id or "main"
    if mid in _CTX_DEVICE:
        return "device"
    if mid in _CTX_SEED:
        return "seed"
    if mid in _CTX_WALLET:
        return "wallet"
    if mid in ("main", "locked", "start_intro_tour"):
        return "main"
    # Unknown ID: inherit from nearest known-context parent in history
    if history:
        for entry in reversed(history):
            parent_id = entry[0] if isinstance(entry, tuple) else entry
            if parent_id and parent_id != mid:
                ctx = _context(parent_id, None)  # one level, no recursion loop
                if ctx != "main":
                    return ctx
    return "main"


def _transition_type(from_ctx, to_ctx, going_back, going_to_main=False):
    """Return ('h_overlay'|'h_push'|'v_overlay', direction) or None.

    Animation direction rules:
    - FORWARD: determined by the DESTINATION context.
        → same context  : H-overlay forward (new slides in from right)
        → device        : H-push enter_device (both screens, device from right)
        → seed/wallet   : V-overlay enter (new slides up from below)
    - BACK / HOME: determined by the SOURCE context (reverse of entry).
        same context    : H-overlay back (old slides out to right)
        from device     : H-push exit_device (both screens, device exits right)
        from seed/wallet: V-overlay exit (old slides down, previous revealed)
    Note: jump_to_context_root() bypasses this function and always uses h_overlay back.
    Note: main→main (same screen) is caught earlier by old_id==new_id guard.
    """
    if going_back or going_to_main:
        # Exiting — animation type determined by what we are leaving
        if from_ctx == to_ctx:
            return ("h_overlay", "back")
        if from_ctx == "device":
            return ("h_push", "exit_device")
        if from_ctx in ("seed", "wallet"):
            return ("v_overlay", "exit")
        return ("h_overlay", "back")  # fallback

    # Forward navigation — animation type determined by destination
    if from_ctx == to_ctx:
        return ("h_overlay", "forward")
    if to_ctx == "device":
        return ("h_push", "enter_device")
    if to_ctx in ("seed", "wallet"):
        return ("v_overlay", "enter")
    return ("h_overlay", "forward")  # fallback: unknown → slide from right
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
    RelatedWalletsForSeedMenu,
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


class SpecterGui(lv.obj):
    # Static tour step definitions: (element_spec, i18n_key, position)
    # element_spec is None, a dotted attribute-path string, or a (x, y, w, h) tuple.
    # Resolved to runtime objects by GuidedTour.resolve_steps() before use.
    INTRO_TOUR_STEPS = [
        (None,                          "TOUR_INTRO",       "center"),
        ("navigation_bar",              "TOUR_WALLET_BAR",  "above"),
        ((435, 143, 28, 28),            "TOUR_HELP_ICON",   "left"),
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
        self._animating = False   # True while a slide animation is running
        self._anim_refs = None    # holds Python callbacks + anim objects alive

        # Navigation bar at bottom (STATUS_BAR_PCT%)
        self.navigation_bar = NavigationBar(self, height_pct=STATUS_BAR_PCT)
        self.navigation_bar.align(lv.ALIGN.BOTTOM_MID, 0, 0)

        # Content area fills from top to just above nav bar (CONTENT_PCT%)
        self.content = lv.obj(self)
        self.content.set_width(lv.pct(100))
        self.content.set_height(lv.pct(CONTENT_PCT))
        self.content.set_layout(lv.LAYOUT.FLEX)
        self.content.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.content.set_style_pad_all(0, 0)
        self.content.set_style_radius(0, 0)
        self.content.set_style_border_width(0, 0)
        self.content.align(lv.ALIGN.TOP_MID, 0, 0)
        # TitledScreen always fills content 100% so no scrolling is needed here
        self.content.set_scroll_dir(lv.DIR.NONE)

        # Create and wire drop-up overlays for Seed and Wallet nav buttons
        self._seed_dropup = SeedDropUp(self)
        self._wallet_dropup = WalletDropUp(self)
        self.navigation_bar.set_seed_dropup(self._seed_dropup)
        self.navigation_bar.set_wallet_dropup(self._wallet_dropup)

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

    def refresh_ui(self):
        """Centralized refresh method for all UI components."""
        self.navigation_bar.refresh()
        # Rebuild drop-ups if open (e.g. after passphrase toggle)
        if hasattr(self, "_seed_dropup") and self._seed_dropup.is_open():
            self._seed_dropup.refresh()
        if hasattr(self, "_wallet_dropup") and self._wallet_dropup.is_open():
            self._wallet_dropup.refresh()

    def show_menu(self, target_menu_id=None):
        # Drop all input while animating
        if self._animating:
            return

        # Close any open drop-up overlays when navigating
        if hasattr(self, "_seed_dropup") and self._seed_dropup.is_open():
            self._seed_dropup.close()
        if hasattr(self, "_wallet_dropup") and self._wallet_dropup.is_open():
            self._wallet_dropup.close()

        going_back = target_menu_id is None
        old_id = self.ui_state.current_menu_id
        old_history = list(self.ui_state.history)

        # Update UIState navigation history
        if going_back:
            seed_snap, wallet_snap = self.ui_state.pop_menu()
            # Only restore snapshots if the objects still exist (e.g. not deleted)
            if seed_snap is not None and seed_snap in self.specter_state.loaded_seeds:
                self.specter_state.active_seed = seed_snap
            elif seed_snap is not None:
                # Snapshot gone — keep whatever is current (or None)
                pass
            if wallet_snap is not None and wallet_snap in self.specter_state.registered_wallets:
                self.specter_state.active_wallet = wallet_snap
        elif target_menu_id == "start_intro_tour":
            self.ui_state.clear_history()
            self.ui_state.current_menu_id = target_menu_id
        elif target_menu_id == "main":
            # Home navigation: clear history and jump to root cleanly.
            # No push — Back after Home must never return to previous menus.
            self.ui_state.clear_history()
            self.ui_state.current_menu_id = "main"
        else:
            self.ui_state.push_menu(
                target_menu_id,
                seed=self.specter_state.active_seed,
                wallet=self.specter_state.active_wallet,
            )

        new_id = self.ui_state.current_menu_id

        # No animation when already on the target menu (e.g. Home pressed on Main).
        # Skip this guard on first call (current_screen is None) so _build_screen runs.
        if old_id == new_id and self.current_screen is not None:
            self.refresh_ui()
            return

        # Compute transition parameters
        from_ctx = _context(old_id, old_history)
        new_history = list(self.ui_state.history)
        to_ctx = _context(new_id, new_history)

        anim_params = None
        if self.current_screen is not None:
            anim_params = _transition_type(from_ctx, to_ctx, going_back,
                                           going_to_main=(new_id == "main"))

        if anim_params is not None:
            self._do_transition(anim_params[0], anim_params[1])
        else:
            if self.current_screen:
                self.current_screen.delete()
                self.current_screen = None
            self._build_screen(new_id)
            self.refresh_ui()

        if self.ui_state.current_menu_id == "start_intro_tour":
            self.ui_state.current_menu_id = "main"
            GuidedTour(self, GuidedTour.resolve_steps(self.INTRO_TOUR_STEPS, self)).start()

    def jump_to_context_root(self, root_menu_id):
        """Jump directly to a context root from any depth within that context.

        Trims all within-context history so that pressing Back from the root
        exits the context cleanly to wherever it was entered from.
        Animates with H-overlay back (sub-screen slides out right).
        No-op if already on the root; falls back to show_menu if not in context.
        """
        if self._animating:
            return

        from_id = self.ui_state.current_menu_id
        root_ctx = _context_direct(root_menu_id)  # device / seed / wallet

        if from_id == root_menu_id:
            # Already at root — do nothing (nav button acts as no-op when at root)
            return

        if _context_direct(from_id) != root_ctx:
            # Not inside this context — use normal forward navigation
            self.show_menu(root_menu_id)
            return

        # Close any open drop-ups
        if hasattr(self, "_seed_dropup") and self._seed_dropup.is_open():
            self._seed_dropup.close()
        if hasattr(self, "_wallet_dropup") and self._wallet_dropup.is_open():
            self._wallet_dropup.close()

        old_id = from_id
        old_history = list(self.ui_state.history)

        # Trim all within-context history entries; keep only pre-context entries.
        # This means pressing Back from root_menu_id exits the context cleanly.
        self.ui_state.history = [
            e for e in self.ui_state.history
            if _context_direct(e[0] if isinstance(e, tuple) else e) != root_ctx
        ]
        # Navigate directly (no push — we don't want "from_id" on the back stack)
        self.ui_state.current_menu_id = root_menu_id

        from_ctx = _context(old_id, old_history)   # always root_ctx
        # Within-context root jump is always h_overlay back
        self._do_transition("h_overlay", "back")
        self.refresh_ui()

    def _build_screen(self, current=None):
        """Instantiate the correct screen class for *current* menu_id."""
        if current is None:
            current = self.ui_state.current_menu_id

        # If the device is locked, always show the locked screen
        if self.specter_state.is_locked:
            self.ui_state.clear_history()
            self.ui_state.current_menu_id = "locked"
            self.current_screen = LockedMenu(self)
            return

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
        elif current == "related_wallets_for_seed":
            self.current_screen = RelatedWalletsForSeedMenu(self)
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
            title = current.replace("_", " ") if current else ""
            title = title[0].upper() + title[1:] if title else ""
            self.current_screen = ActionScreen(title, self)

    def _do_transition(self, anim_type, direction):
        """Animate from the current screen to a freshly-built new screen.

        anim_type  : 'h_overlay' | 'h_push' | 'v_overlay'
        direction  : 'forward' | 'back'             (h_overlay)
                     'enter_device' | 'exit_device'  (h_push)
                     'enter' | 'exit'                (v_overlay)
        """
        old_screen = self.current_screen
        if old_screen is None:
            self._build_screen()
            self.refresh_ui()
            return

        W = SCREEN_WIDTH
        nav_h = SCREEN_HEIGHT * STATUS_BAR_PCT // 100
        content_h = SCREEN_HEIGHT - nav_h

        # Switch content to absolute layout so we can position screens manually
        self.content.set_layout(lv.LAYOUT.NONE)
        self.current_screen = None

        # Build the incoming screen (parented into self.content)
        self._build_screen()
        new_screen = self.current_screen

        if new_screen is None:
            # Abort gracefully
            self.current_screen = old_screen
            self.content.set_layout(lv.LAYOUT.FLEX)
            self.content.set_flex_flow(lv.FLEX_FLOW.COLUMN)
            return

        # Give both screens the full content area
        old_screen.set_size(W, content_h)
        new_screen.set_size(W, content_h)
        old_screen.set_pos(0, 0)

        self._animating = True
        refs = []

        # ── H-overlay: only new/old screen moves ─────────────────────────────
        if anim_type == "h_overlay":
            if direction == "forward":
                new_screen.set_x(W)
                cb = lambda anim, v: new_screen.set_x(v)
                a = lv.anim_t(); a.init()
                a.set_custom_exec_cb(cb); a.set_values(W, 0)
                a.set_duration(ANIM_MS); a.start()
                refs.extend([cb, a])
            else:  # back
                new_screen.set_x(0)
                old_screen.move_foreground()  # old must be on top so its slide-out is visible
                cb = lambda anim, v: old_screen.set_x(v)
                a = lv.anim_t(); a.init()
                a.set_custom_exec_cb(cb); a.set_values(0, W)
                a.set_duration(ANIM_MS); a.start()
                refs.extend([cb, a])
            anim_done_ms = ANIM_MS

        # ── H-push: both screens move simultaneously ──────────────────────────
        elif anim_type == "h_push":
            if direction == "enter_device":
                new_screen.set_x(W)
                cb_n = lambda anim, v: new_screen.set_x(v)
                cb_o = lambda anim, v: old_screen.set_x(v)
                for cb, vs, ve in [(cb_n, W, 0), (cb_o, 0, -W)]:
                    a = lv.anim_t(); a.init()
                    a.set_custom_exec_cb(cb); a.set_values(vs, ve)
                    a.set_duration(ANIM_MS); a.start()
                    refs.extend([cb, a])
            else:  # exit_device
                new_screen.set_x(-W)
                cb_n = lambda anim, v: new_screen.set_x(v)
                cb_o = lambda anim, v: old_screen.set_x(v)
                for cb, vs, ve in [(cb_n, -W, 0), (cb_o, 0, W)]:
                    a = lv.anim_t(); a.init()
                    a.set_custom_exec_cb(cb); a.set_values(vs, ve)
                    a.set_duration(ANIM_MS); a.start()
                    refs.extend([cb, a])
            anim_done_ms = ANIM_MS

        # ── V-overlay: vertical slide; nav bar always stays on top ────────────
        else:  # v_overlay
            # Make content background transparent so nav bar shows through
            self.content.set_style_bg_opa(lv.OPA.TRANSP, 0)
            # Allow screens to temporarily render outside content bounds
            self.content.add_flag(lv.obj.FLAG.OVERFLOW_VISIBLE)
            # Ensure nav bar stays above the content during animation
            self.navigation_bar.move_foreground()

            if direction == "enter":
                # New slides up from below; old stays
                new_screen.set_y(content_h)
                cb = lambda anim, v: new_screen.set_y(v)
                a = lv.anim_t(); a.init()
                a.set_custom_exec_cb(cb)
                a.set_values(content_h, 0)
                a.set_duration(ANIM_MS_VERTICAL); a.start()
                refs.extend([cb, a])
            else:  # exit
                # Old slides down to reveal new which is already in place
                new_screen.set_y(0)
                old_screen.move_foreground()  # old must cover new while sliding away
                cb = lambda anim, v: old_screen.set_y(v)
                a = lv.anim_t(); a.init()
                a.set_custom_exec_cb(cb)
                a.set_values(0, content_h)
                a.set_duration(ANIM_MS_VERTICAL); a.start()
                refs.extend([cb, a])
            anim_done_ms = ANIM_MS_VERTICAL

        # ── Cleanup timer ─────────────────────────────────────────────────────
        old_s   = old_screen
        new_s   = new_screen
        content = self.content
        gui     = self
        is_vert = anim_type == "v_overlay"

        def _on_done(timer):
            timer.delete()
            gui._animating = False
            gui._anim_refs = None
            if is_vert:
                content.remove_flag(lv.obj.FLAG.OVERFLOW_VISIBLE)
                content.set_style_bg_opa(lv.OPA.COVER, 0)
            content.set_layout(lv.LAYOUT.FLEX)
            content.set_flex_flow(lv.FLEX_FLOW.COLUMN)
            new_s.set_pos(0, 0)
            try:
                old_s.delete()
            except Exception:
                pass
            gui.refresh_ui()

        t = lv.timer_create(_on_done, anim_done_ms + 50, None)
        refs.extend([_on_done, t])
        self._anim_refs = refs
