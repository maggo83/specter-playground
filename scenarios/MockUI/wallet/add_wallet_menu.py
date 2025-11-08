from ..basic import GenericMenu
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
            (lv.SYMBOL.LIST, "Generate New Seedphrase", "generate_seedphrase", None),
            (lv.SYMBOL.UPLOAD, "Import Seedphrase from", None, None),
        ]

        # conditional import sources
        if state and state.hasSmartCard and state.enabledSmartCard and state.detectedSmartCard:
            menu_items.append((None, "SmartCard", "import_from_smartcard", None))

        if state and state.hasQR and state.enabledQR:
            menu_items.append((None, "QR Code", "import_from_qr", None))

        if state and state.hasSD and state.enabledSD and state.detectedSD:
            menu_items.append((lv.SYMBOL.SD_CARD, "SD Card", "import_from_sd", None))

        menu_items += [
            (lv.SYMBOL.DIRECTORY, "internal Flash", "import_from_flash", None),
            (lv.SYMBOL.KEYBOARD, "Keyboard", "import_from_keyboard", None),
        ]

        super().__init__("add_wallet", lv.SYMBOL.PLUS + " Add Wallet", menu_items, parent, *args, **kwargs)
