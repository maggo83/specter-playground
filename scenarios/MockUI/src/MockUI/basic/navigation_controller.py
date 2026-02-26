import lvgl as lv

from ..helpers import UIState, SpecterState
from .device_bar import DeviceBar
from .wallet_bar import WalletBar
from .action_screen import ActionScreen
from .main_menu import MainMenu
from .locked_menu import LockedMenu
from ..wallet import (
    WalletMenu,
    ConnectWalletsMenu,
    ChangeWalletMenu,
    AddWalletMenu,
    SeedPhraseMenu,
    GenerateSeedMenu,
    PassphraseMenu,
)
from ..device import (
    DeviceMenu,
    BackupsMenu,
    FirmwareMenu,
    InterfacesMenu,
    StorageMenu,
    SecurityMenu,
    LanguageMenu,
    SettingsMenu,
)
from ..i18n import I18nManager
from ..tour import GuidedTour


class NavigationController(lv.obj):
    def __init__(self, specter_state=None, ui_state=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        # Create device bar at top (5%), wallet bar at bottom (5%), and content in middle (90%)
        self.device_bar = DeviceBar(self, height_pct=5)
        self.device_bar.align(lv.ALIGN.TOP_MID, 0, 0)

        # Wallet bar at bottom
        self.wallet_bar = WalletBar(self, height_pct=5)
        self.wallet_bar.align(lv.ALIGN.BOTTOM_MID, 0, 0)

        # Content area in middle (scrollable)
        self.content = lv.obj(self)
        self.content.set_width(lv.pct(100))
        self.content.set_height(lv.pct(90))
        self.content.set_layout(lv.LAYOUT.FLEX)
        self.content.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.content.set_style_pad_all(0, 0)
        self.content.set_style_radius(0, 0)
        self.content.set_style_border_width(0, 0)
        self.content.align_to(self.device_bar, lv.ALIGN.OUT_BOTTOM_MID, 0, 0)
        # Enable scrolling for content area
        self.content.set_scroll_dir(lv.DIR.VER)

        # initially show the main menu
        self.show_menu(None)
        
        # Start guided tour on first startup (after UI is fully constructed)
        if self.ui_state.run_tour_on_startup:
            GuidedTour(self).start()

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

        # Update UIState navigation history when present
        if target_menu_id is not None:
            # navigating 'down' into target
            self.ui_state.push_menu(target_menu_id)
        else:
            # when moving up/back, pop to previous menu
            self.ui_state.pop_menu()

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
        if current == "main":
            self.current_screen = MainMenu(self)
        elif current == "manage_wallet":
            self.current_screen = WalletMenu(self)
        elif current == "manage_device":
            self.current_screen = DeviceMenu(self)
        elif current == "manage_backups":
            self.current_screen = BackupsMenu(self)
        elif current == "manage_firmware":
            self.current_screen = FirmwareMenu(self)
        elif current == "connect_sw_wallet":
            self.current_screen = ConnectWalletsMenu(self)
        elif current == "change_wallet":
            self.current_screen = ChangeWalletMenu(self)
        elif current == "add_wallet":
            self.current_screen = AddWalletMenu(self)
        elif current == "manage_security":
            self.current_screen = SecurityMenu(self)
        elif current == "interfaces":
            self.current_screen = InterfacesMenu(self)
        elif current == "manage_seedphrase":
            self.current_screen = SeedPhraseMenu(self)
        elif current == "generate_seedphrase":
            self.current_screen = GenerateSeedMenu(self)
        elif current == "set_passphrase":
            self.current_screen = PassphraseMenu(self)
        elif current == "manage_storage":
            self.current_screen = StorageMenu(self)
        elif current == "select_language":
            self.current_screen = LanguageMenu(self)
        elif current == "manage_settings":
            self.current_screen = SettingsMenu(self)
        else:
            # For all other actions, show a generic action screen
            title = (target_menu_id or "").replace("_", " ")
            title = title[0].upper() + title[1:] if title else ""
            self.current_screen = ActionScreen(title, self)

        # refresh the UI
        self.refresh_ui()
