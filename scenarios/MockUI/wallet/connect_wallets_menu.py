from ..basic import GenericMenu
import lvgl as lv

class ConnectWalletsMenu(GenericMenu):
    """Menu to connect or export to software wallets.

    menu_id: "connect_sw_wallet"
    """

    def __init__(self, parent, *args, **kwargs):
        # the actual connection logic is out of scope here; provide menu entries
        menu_items = [
            (None, "Sparrow", "connect_sparrow", None),
            (None, "Nunchuck", "connect_nunchuck", None),
            (None, "BlueWallet", "connect_bluewallet", None),
            (None, "Other...", "connect_other", None),
        ]

        title = "Connect SW Wallet"
        super().__init__("connect_sw_wallet", title, menu_items, parent, *args, **kwargs)
