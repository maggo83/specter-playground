from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS
from ..basic.widgets import MenuItem
from ..stubs import Seed
import lvgl as lv

class ViewSignersScreen(GenericMenu):
    """Form to view the active seed's signers.

    menu_id: "view_signers"
    """

    TITLE_KEY = "WALLET_MENU_VIEW_SIGNERS"

    def get_menu_items(self, t, state):
        """Show list of signers for the active seed."""
        s4w = state.seeds_for_wallet(self.ui_state.active_wallet)
        loaded_fp4w = Seed.get_fingerprints(s4w) if s4w else []

        menu_items = []
        for fp in self.ui_state.active_wallet.required_fingerprints:
            signer_name = fp[2:]  # do not show "0x" hex prefix in fingerprint
            icon = None
            target = None

            if s4w and fp in loaded_fp4w:
                matched_seed = s4w[loaded_fp4w.index(fp)]
                signer_name += " (" + matched_seed.label + ")"
                icon = BTC_ICONS.CHECK

                def _make_seed_cb(seed):
                    def _cb(e):
                        if e.get_code() != lv.EVENT.CLICKED:
                            return
                        self.ui_state.set_active_seed(seed)
                        self.on_navigate("manage_seedphrase")
                    return _cb

                target = _make_seed_cb(matched_seed)

            menu_items.append(MenuItem(icon, signer_name, target=target))
        return menu_items
    
    def post_init(self, t, state):
        """Add wallet name to title."""
        title = self.title.get_text()
        title += "," + self.ui_state.active_wallet.label
        self.title.set_text(title)

