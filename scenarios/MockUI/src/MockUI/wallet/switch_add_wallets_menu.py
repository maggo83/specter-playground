from ..basic import SwitchAddMenu


class SwitchAddWalletsMenu(SwitchAddMenu):
    """Switch/Add menu showing Wallets, grouped by seed compatibility.

    When all registered wallets are compatible with the active seed, the list is
    shown flat (no section headers). When there are wallets that do *not* match
    the active seed, the list is split into two labelled sections:
        1. "Wallets for active seed"  — wallets usable with the currently loaded seed
        2. "Other wallets"            — remaining registered wallets
    """

    TITLE_KEY = "MENU_SWITCH_ADD_WALLET"

    def get_menu_items(self, t, state):
        seed_wallets = self.state.wallets_for_seed(state.active_seed) or []
        other_wallets = [w for w in state.registered_wallets if w not in seed_wallets]
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
            )

        if seed_wallets:
            if other_wallets:
                return (
                    [(None, t("ADD_SWITCH_WALLET_MENU_WALLETS_FOR_SEED"), None, None, None, None)]
                    + items(seed_wallets)
                    + [(None, t("ADD_SWITCH_WALLET_MENU_OTHER_WALLETS"), None, None, None, None)]
                    + items(other_wallets, "add_wallet", t("MENU_ADD_WALLET"))
                )
            else:
                return items(seed_wallets, "add_wallet", t("MENU_ADD_WALLET"))
        else:
            if other_wallets:
                return items(other_wallets, "add_wallet", t("MENU_ADD_WALLET"))
            else:
                return []