import lvgl as lv

from ..stubs import UIState, SpecterState
from .device_bar import DeviceBar
from .wallet_bar import WalletBar
from .action_screen import ActionScreen
from .main_menu import MainMenu
from .locked_menu import LockedMenu
from .ui_consts import STATUS_BAR_PCT, CONTENT_PCT
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
        ("device_bar.lock_btn",         "TOUR_LOCK",        "below"),
        ("device_bar.center_container", "TOUR_INTERFACES",  "below"),
        ("device_bar.batt_icon",        "TOUR_BATTERY",     "below"),
        ("device_bar.power_btn",        "TOUR_POWER",       "below"),
        ("wallet_bar",                  "TOUR_WALLET_BAR",  "above"),
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

        # Create device bar at top (STATUS_BAR_PCT%), wallet bar at bottom (STATUS_BAR_PCT%), content in middle (CONTENT_PCT%)
        self.device_bar = DeviceBar(self, height_pct=STATUS_BAR_PCT)
        self.device_bar.align(lv.ALIGN.TOP_MID, 0, 0)

        # Wallet bar at bottom
        self.wallet_bar = WalletBar(self, height_pct=STATUS_BAR_PCT)
        self.wallet_bar.align(lv.ALIGN.BOTTOM_MID, 0, 0)

        # Content area in middle (scrollable)
        self.content = lv.obj(self)
        self.content.set_width(lv.pct(100))
        self.content.set_height(lv.pct(CONTENT_PCT))
        self.content.set_layout(lv.LAYOUT.FLEX)
        self.content.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.content.set_style_pad_all(0, 0)
        self.content.set_style_radius(0, 0)
        self.content.set_style_border_width(0, 0)
        self.content.align_to(self.device_bar, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)
        # TitledScreen always fills content 100% so no scrolling is needed here
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

    def refresh_ui(self):
        """Centralized refresh method for all UI components."""
        self.device_bar.refresh(self.specter_state)
        self.wallet_bar.refresh(self.specter_state)

    def show_menu(self, target_menu_id=None):
        
        # Delete current screen (free memory)
        if self.current_screen:
            self.current_screen.delete()

        # Update UIState navigation history
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

        # If the device is locked, always show the locked screen
        if self.specter_state.is_locked:
            # ensure the ui history is cleared when locking
            self.ui_state.clear_history()
            self.ui_state.current_menu_id = "locked"
            self.current_screen = LockedMenu(self)
            self.refresh_ui()
            return

        # Create new screen (micropython doesn't support match/case)
        current = self.ui_state.current_menu_id
        if current in ("main", "start_intro_tour"):
            self.current_screen = MainMenu(self)
        elif current == "manage_wallet":
            self.current_screen = WalletMenu(self)
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
            title = (target_menu_id or "").replace("_", " ")
            title = title[0].upper() + title[1:] if title else ""
            self.current_screen = ActionScreen(title, self)

        # refresh the UI
        self.refresh_ui()

        # If this was a start_intro_tour action, launch the tour overlay now.
        # Reset current_menu_id to "main" BEFORE starting the tour so that
        # "start_intro_tour" is never left in the history stack.  Without this,
        # navigating away from the main menu (e.g. into WalletMenu) pushes
        # "start_intro_tour" onto history, and popping back triggers the tour
        # again even if the user already skipped it.
        if self.ui_state.current_menu_id == "start_intro_tour":
            self.ui_state.current_menu_id = "main"
            GuidedTour(self, GuidedTour.resolve_steps(self.INTRO_TOUR_STEPS, self)).start()
