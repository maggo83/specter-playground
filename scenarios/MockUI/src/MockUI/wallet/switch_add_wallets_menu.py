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
        common = dict(
            label_creation_cb=lambda w: w.label,
            active_element=state.active_wallet,
            activation_cb=self.state.set_active_wallet,
            show_check=len(seed_wallets) + len(other_wallets) > 1,
        )

        if not other_wallets:
            return super().get_menu_items(
                t, state, elements=seed_wallets, **common,
                add_target_behavior="add_wallet", add_string=t("MENU_ADD_WALLET"),
            )

        return (
            [(None, t("ADD_SWITCH_WALLET_MENU_WALLETS_FOR_SEED"), None, None, None, None)]
            + super().get_menu_items(t, state, elements=seed_wallets, **common)
            + [(None, t("ADD_SWITCH_WALLET_MENU_OTHER_WALLETS"), None, None, None, None)]
            + super().get_menu_items(
                t, state, elements=other_wallets, **common,
                add_target_behavior="add_wallet", add_string=t("MENU_ADD_WALLET"),
            )
        )