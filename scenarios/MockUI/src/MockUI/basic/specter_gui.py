import lvgl as lv

from ..stubs import UIState, SpecterState
from .device_bar import DeviceBar
from .select_and_manage_bar import SelectAndManageSeedsBar, SelectAndManageWalletsBar
from .action_screen import ActionScreen
from .main_menu import MainMenu
from .locked_menu import LockedMenu
from .ui_consts import STATUS_BAR_PCT, SELECT_BAR_PCT, CONTENT_PCT, SCREEN_HEIGHT
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
    # Device menus: both select bars hidden
    _DEVICE_MENUS = frozenset([
        "manage_settings", "manage_security_settings", "manage_backups",
        "manage_firmware", "interfaces", "manage_storage", "select_language",
        "manage_preferences", "manage_security_features",
        # Adding/creating a new seed has no active seed context → hide seed bar too
        "add_seed", "generate_seedphrase",
    ])
    # Seed menus: wallet bar hidden (seeds bar may still be useful for context)
    _SEED_MENUS = frozenset([
        "switch_add_seeds",
        "manage_seedphrase", "store_seedphrase", "clear_seedphrase",
        "set_passphrase",
        # Adding/creating a wallet has no active wallet context → hide wallet bar
        "add_wallet", "create_custom_wallet",
    ])

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

        # Update UIState navigation history (before building screen)
        if target_menu_id is None:
            # navigating up/back: pop previous menu from history
            self.ui_state.pop_menu()
        elif target_menu_id == "start_intro_tour":
            # special action: clear history and set current directly, no push
            self.ui_state.clear_history()
            self.ui_state.current_menu_id = target_menu_id
        else:
            # navigating down into a new menu
            self.ui_state.push_menu(target_menu_id)

        # refresh_ui rebuilds current_screen + bars + layout
        self.refresh_ui()

        # If this was a start_intro_tour action, launch the tour overlay now.
        # Reset current_menu_id to "main" BEFORE starting the tour so that
        # "start_intro_tour" is never left in the history stack.
        if self.ui_state.current_menu_id == "start_intro_tour":
            self.ui_state.current_menu_id = "main"
            GuidedTour(self, GuidedTour.resolve_steps(self.INTRO_TOUR_STEPS, self)).start()
