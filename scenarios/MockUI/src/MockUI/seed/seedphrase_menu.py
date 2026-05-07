from ..basic import ORANGE_HEX, RED_HEX, WHITE_HEX, GenericMenu, TITLE_ROW_HEIGHT
from ..basic.symbol_lib import BTC_ICONS
from ..basic.keyboard_manager import Layout
from ..basic.widgets.action_modal import ActionModal
from ..basic.confirm_modals import confirm_delete_seed
from ..basic.widgets import Btn, title_textarea, MenuItem
import lvgl as lv

class SeedPhraseMenu(GenericMenu):
    """Manage Seedphrase menu — includes passphrase, storage, and advanced options.

    menu_id: "manage_seedphrase"
    """
    TITLE_KEY = "MENU_MANAGE_SEED"

    def get_menu_items(self, t, state):
        menu_items = []

        menu_items.append(MenuItem(BTC_ICONS.VISIBLE, t("SEEDPHRASE_MENU_SHOW"), "show_seedphrase", color=ORANGE_HEX))

        pp_label = t("MENU_CHANGE_CLEAR_PASSPHRASE") if self.ui_state.active_seed.passphrase else t("MENU_SET_PASSPHRASE")
        menu_items.append(MenuItem(BTC_ICONS.PASSWORD, pp_label, "set_passphrase", is_submenu=True))

        menu_items.append(MenuItem(text=t("SEEDPHRASE_MENU_STORAGE")))
        menu_items.append(MenuItem(lv.SYMBOL.DOWNLOAD, t("SEEDPHRASE_MENU_STORE_TO") + "...", "store_seedphrase", is_submenu=True))
        menu_items.append(MenuItem(BTC_ICONS.TRASH, t("SEEDPHRASE_MENU_CLEAR_FROM") + "...", "clear_seedphrase", color=RED_HEX, is_submenu=True))

        menu_items.append(MenuItem(text=t("SEEDPHRASE_MENU_ADVANCED")))
        menu_items.append(MenuItem(BTC_ICONS.SHARED_WALLET, t("SEEDPHRASE_MENU_BIP85"), "derive_bip85"))

        # Explore section
        menu_items.append(MenuItem(text=t("SEEDPHRASE_MENU_EXPLORE")))
        menu_items.append(MenuItem(BTC_ICONS.WALLET, t("SEEDPHRASE_MENU_RELATED_WALLETS"), "related_wallets_for_seed", is_submenu=True))

        # Sign message (only when signing is possible)
        has_controlled_input = (state.QR_enabled() or state.SD_detected())
        can_sign_msg = (
            len(state.registered_wallets) > 0
            and not all(wallet.isMultiSig for wallet in state.registered_wallets)
            and has_controlled_input
        )
        if can_sign_msg:
            menu_items.append(MenuItem(BTC_ICONS.SIGN, t("MAIN_MENU_SIGN_MESSAGE"), "sign_message"))

        return menu_items

    def post_init(self, t, state):
        # Replace the default title label with editable text area + delete button
        # (same pattern as WalletMenu)
        self.title.delete()

        # Text area for seed name (editable) – lives in title_bar, centred
        self.name_textarea = title_textarea(self.title_bar)
        self.name_textarea.set_text(self.ui_state.active_seed.label)

        textarea_height = self.name_textarea.get_height()

        # Key icon (transparent, non-clickable) – left of textarea
        self.icon_btn = Btn(
            self.title_bar,
            icon=BTC_ICONS.KEY,
            size=(textarea_height, textarea_height),
        )
        self.icon_btn.make_background_transparent()
        self.icon_btn._btn.remove_flag(lv.obj.FLAG.CLICKABLE)
        self.icon_btn.align_to(self.name_textarea, lv.ALIGN.OUT_LEFT_MID, -6, 0)

        # Red trash button – square, matching textarea height
        self.delete_btn = Btn(
            self.title_bar,
            icon=BTC_ICONS.TRASH,
            color=RED_HEX,
            size=(textarea_height, textarea_height),
        )
        self.delete_btn.align_to(self.name_textarea, lv.ALIGN.OUT_RIGHT_MID, 6, 0)

        def _on_commit(new_name):
            self.ui_state.active_seed.label = new_name
            self.gui.refresh_ui()

        keyboard_binder = lambda e: self.gui.keyboard_manager.bind(
            self.name_textarea, Layout.FULL, _on_commit
        )
        self.name_textarea.add_event_cb(keyboard_binder, lv.EVENT.CLICKED, None)

        # Trash button shows delete confirmation popup
        def _on_delete(e):
            if e.get_code() != lv.EVENT.CLICKED:
                return
            seed = self.ui_state.active_seed

            def _do_delete():
                self.device_state.remove_seed(seed)
                self.ui_state.active_seed = None
                self.gui.ui_state.clear_history()
                self.gui.ui_state.current_menu_id = "main"
                self.gui.refresh_ui()
                self.on_navigate(None)

            confirm_delete_seed(t, seed.label, _do_delete)

        self.delete_btn.add_event_cb(_on_delete, lv.EVENT.CLICKED, None)
