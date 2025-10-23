from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS
import lvgl as lv

class AddWalletMenu(GenericMenu):
    """Menu to create or import a wallet.

    Menu items:
    - Generate New Seedphrase
    - Import Seedphrase from: SmartCard, QR Code, SD Card, internal Flash, Keyboard
      Conditional items included according to parent.specter_state flags.
    """

    def __init__(self, parent, *args, **kwargs):
        state = getattr(parent, "specter_state", None)

        menu_items = [
            (BTC_ICONS.MNEMONIC, "Generate New Seedphrase", "generate_seedphrase", None),
            (None, "Import Seedphrase from", None, None),
        ]

        # conditional import sources
        if state and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard:
            menu_items.append((BTC_ICONS.SMARTCARD, "SmartCard", "import_from_smartcard", None))

        if state and state.hasQR and state.enabledQR:
            menu_items.append((BTC_ICONS.QR_CODE, "QR Code", "import_from_qr", None))

        if state and state.hasSD and state.enabledSD and state.detectedSD:
            menu_items.append((BTC_ICONS.SD_CARD, "SD Card", "import_from_sd", None))

        menu_items += [
            (BTC_ICONS.FILE, "internal Flash", "import_from_flash", None),
            (lv.SYMBOL.KEYBOARD, "Keyboard", "import_from_keyboard", None),
        ]

        super().__init__("add_wallet", "Add Wallet", menu_items, parent, *args, **kwargs)
