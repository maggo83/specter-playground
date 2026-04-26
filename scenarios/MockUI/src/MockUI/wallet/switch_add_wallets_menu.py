from ..basic import SwitchAddMenu
from ..basic.widgets import MenuItem
from ..basic.symbol_lib import BTC_ICONS
from ..basic.ui_consts import WHITE_HEX
from ..basic.select_and_manage_bar import wallet_key_color


def _sort_wallets(wallets):
    """Sort: default first → singlesig (by name) → multisig (by threshold then name) → custom (by name)."""
    default   = [w for w in wallets if w.is_default_wallet()]
    singlesig = sorted(
        [w for w in wallets if not w.is_default_wallet() and not w.isMultiSig and w.is_standard()],
        key=lambda w: w.label.lower()
    )
    multisig  = sorted(
        [w for w in wallets if w.isMultiSig],
        key=lambda w: (w.threshold or 0, w.label.lower())
    )
    custom    = sorted(
        [w for w in wallets if not w.is_default_wallet() and not w.isMultiSig and not w.is_standard()],
        key=lambda w: w.label.lower()
    )
    return default + singlesig + multisig + custom


class SwitchAddWalletsMenu(SwitchAddMenu):
    """Switch/Add menu showing Wallets, grouped by seed compatibility.

    When all registered wallets are compatible with the active seed, the list is
    shown flat (no section headers). When there are wallets that do *not* match
    the active seed, the list is split into two labelled sections:
        1. "Wallets for active seed"  — wallets usable with the currently loaded seed
        2. "Other wallets"            — remaining registered wallets
    """

    TITLE_KEY = "MENU_SWITCH_ADD_WALLET"

    def _wallet_suffix(self, wallet):
        """Build right-side suffix info for a wallet list item."""
        key_color = wallet_key_color(self.state, wallet)

        if not wallet.is_standard():
            type_icon = BTC_ICONS.CONSOLE
        elif wallet.isMultiSig:
            type_icon = BTC_ICONS.TWO_KEYS
        else:
            type_icon = BTC_ICONS.KEY

        net_map = {"mainnet": "main", "testnet": "test", "signet": "sig"}
        net_text = net_map.get(wallet.net, wallet.net)

        suffix = [(type_icon, key_color, None), (None, None, net_text)]
        if wallet.isMultiSig and wallet.threshold:
            nm = "%d/%d" % (wallet.threshold, len(wallet.required_fingerprints))
            suffix.append((None, None, nm))
        return suffix

    def get_menu_items(self, t, state):
        seed_wallets = _sort_wallets(
            self.state.wallets_for_seed(state.active_seed) or []
        )
        other_wallets = _sort_wallets(
            [w for w in state.registered_wallets if w not in seed_wallets]
        )
        show_check = len(seed_wallets) + len(other_wallets) > 1

        def items(wallets, add_behavior=None, add_str=None):
            return super(SwitchAddWalletsMenu, self).get_menu_items(
                elements=wallets,
                label_creation_cb=lambda w: w.label,
                active_element=state.active_wallet,
                activation_cb=self.state.set_active_wallet,
                show_check=show_check,
                add_target_behavior=add_behavior,
                add_string=add_str,
                suffix_cb=self._wallet_suffix,
            )

        if seed_wallets:
            if other_wallets:
                return (
                    [MenuItem(text=t("ADD_SWITCH_WALLET_MENU_WALLETS_FOR_SEED"))]
                    + items(seed_wallets)
                    + [MenuItem(text=t("ADD_SWITCH_WALLET_MENU_OTHER_WALLETS"))]
                    + items(other_wallets, "add_wallet", t("MENU_ADD_WALLET"))
                )
            else:
                return items(seed_wallets, "add_wallet", t("MENU_ADD_WALLET"))
        else:
            if other_wallets:
                return items(other_wallets, "add_wallet", t("MENU_ADD_WALLET"))
            else:
                return []