# MockUI/__init__.py
from .basic import BTN_HEIGHT, BTN_WIDTH, MENU_PCT, PAD_SIZE, SWITCH_HEIGHT, SWITCH_WIDTH, STATUS_BTN_HEIGHT, STATUS_BTN_WIDTH, ONE_LETTER_SYMBOL_WIDTH, TWO_LETTER_SYMBOL_WIDTH, THREE_LETTER_SYMBOL_WIDTH, GREEN, ORANGE, RED
from .basic import MainMenu, LockedMenu, DeviceBar, WalletBar, ActionScreen, GenericMenu
from .basic import SpecterGui
from .tour import UIExplainer, GuidedTour

from .stubs import UIState, SpecterState, Wallet, Seed

from .wallet import (
    WalletMenu,
    AddWalletMenu,
    ConnectWalletsMenu,
    SeedPhraseMenu,
    GenerateSeedMenu,
    PassphraseMenu,
)

from .device import (
    SecuritySettingsMenu,
    FirmwareMenu,
    InterfacesMenu,
    BackupsMenu,
    SecurityFeaturesMenu,
    StorageMenu,
    SettingsMenu,
    PreferencesMenu,
)

from .tour import GuidedTour

__all__ = [
    "BTN_HEIGHT", "BTN_WIDTH",
    "MENU_PCT",
    "PAD_SIZE",
    "SWITCH_HEIGHT", "SWITCH_WIDTH",
    "STATUS_BTN_HEIGHT", "STATUS_BTN_WIDTH",
    "ONE_LETTER_SYMBOL_WIDTH", "TWO_LETTER_SYMBOL_WIDTH", "THREE_LETTER_SYMBOL_WIDTH",
    "GREEN", "ORANGE", "RED",
    "MainMenu",
    "WalletMenu",
    "SecuritySettingsMenu",
    "SpecterState",
    "Wallet",
    "Seed",
    "ActionScreen",
    "UIState",
    "DeviceBar",
    "WalletBar",
    "SeedPhraseMenu",
    "SecurityFeaturesMenu",
    "InterfacesMenu",
    "BackupsMenu",
    "FirmwareMenu",
    "ConnectWalletsMenu",
    "AddWalletMenu",
    "LockedMenu",
    "GenerateSeedMenu",
    "StorageMenu",
    "SettingsMenu",
    "PassphraseMenu",
    "SpecterGui",
    "UIExplainer",
    "GuidedTour",
]