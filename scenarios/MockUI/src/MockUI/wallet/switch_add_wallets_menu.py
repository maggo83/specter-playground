from ..basic import SwitchAddMenu

class SwitchAddWalletsMenu(SwitchAddMenu):
    """Switch/Add menu showing only Wallets."""
    TITLE_KEY = "MENU_SWITCH_ADD_WALLET"

    def get_menu_items(self, t, state):
        return super().get_menu_items(
            t, state,
            elements=state.registered_wallets,
            label_creation_cb=lambda wallet: wallet.label,
            active_element=state.active_wallet,
            activation_cb= lambda wallet: self.state.set_active_wallet(wallet),
            add_target_behavior="add_wallet",
            add_string=t("MENU_ADD_WALLET")
        )