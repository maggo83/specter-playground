from ..basic import GenericMenu
from ..basic.symbol_lib import BTC_ICONS


class ManageSeedsAndWalletsMenu(GenericMenu):
    """Combined menu: manage and switch/add for both seeds and wallets.

    menu_id: "manage_seeds_and_wallets"
    Shows 4 items:
      Seeds:
        1. Manage Seed
        2. Switch/Add Seed  (or "Add Seed" when only 1 loaded)
      Wallet:
        3. Manage Wallet
        4. Switch/Add Wallet  (or "Add Wallet" when only 1 registered)
    """

    TITLE_KEY = "MAIN_MENU_MANAGE_SEED_WALLET"

    def get_menu_items(self, t, state):
        menu_items = []
        num_seeds = len(state.loaded_seeds)
        num_wallets = len(state.registered_wallets)

        # ── Seed / MasterKey section ────────────────────────────────────────
        menu_items.append((None, t("MANAGE_SW_SEED_SECTION_TITLE"), None, None, None, None))
        menu_items.append((BTC_ICONS.MNEMONIC, t("MENU_MANAGE_SEED"), "manage_seedphrase", None, None, None))
        if num_seeds > 1:
            menu_items.append((BTC_ICONS.REFRESH, t("MENU_SWITCH_ADD_SEED"), "switch_add_seeds", None, None, None))
        else:
            menu_items.append((BTC_ICONS.PLUS, t("MENU_ADD_SEED"), "add_seed", None, None, None))

        # ── Wallet section ──────────────────────────────────────────────────
        menu_items.append((None, t("MANAGE_SW_WALLET_SECTION_TITLE"), None, None, None, None))
        if state and state.active_wallet is not None:
            menu_items.append((BTC_ICONS.WALLET, t("MENU_MANAGE_WALLET"), "manage_wallet", None, None, None))
        if num_wallets > 1:
            menu_items.append((BTC_ICONS.REFRESH, t("MENU_SWITCH_ADD_WALLET"), "switch_add_wallets", None, None, None))
        else:
            menu_items.append((BTC_ICONS.PLUS, t("MENU_ADD_WALLET"), "add_wallet", None, None, None))

        return menu_items
