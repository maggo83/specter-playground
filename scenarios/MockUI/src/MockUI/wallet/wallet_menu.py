from ..basic import RED_HEX, WHITE_HEX, GenericMenu, RED, ORANGE, TITLE_ROW_HEIGHT
from ..basic.symbol_lib import BTC_ICONS
from ..basic.keyboard_manager import Layout
from ..basic.widgets.action_modal import ActionModal
from ..basic.widgets import Btn, title_textarea, MenuItem
from ..basic.ui_consts import BTN_HEIGHT, BTN_WIDTH
import lvgl as lv


class WalletMenu(GenericMenu):
    """Menu for managing an active wallet with editable name."""

    TITLE_KEY = "MENU_MANAGE_WALLET"

    def get_menu_items(self, t, state):
        menu_items = []

        menu_items.append(MenuItem(text=t("WALLET_MENU_EXPLORE")))
        menu_items.append(MenuItem(BTC_ICONS.MENU, t("WALLET_MENU_VIEW_ADDRESSES"), "view_addresses"))
        if (state.active_wallet and state.active_wallet.isMultiSig):
            menu_items.append(MenuItem(BTC_ICONS.ADDRESS_BOOK, t("WALLET_MENU_VIEW_SIGNERS"), "view_signers"))

        menu_items.append(MenuItem(text=t("WALLET_MENU_MANAGE")))
        menu_items.append(MenuItem(BTC_ICONS.CONSOLE, t("WALLET_MENU_MANAGE_DESCRIPTOR"), "manage_wallet_descriptor"))
        menu_items.append(MenuItem(BTC_ICONS.BITCOIN, t("WALLET_MENU_CHANGE_NETWORK"), "change_network"))

        menu_items += [
            MenuItem(text=t("WALLET_MENU_CONNECT_EXPORT")),
            MenuItem(BTC_ICONS.LINK, t("MENU_CONNECT_SW_WALLET"), "connect_sw_wallet"),
            MenuItem(BTC_ICONS.EXPORT, t("WALLET_MENU_EXPORT_DATA"), "export_wallet"),
        ]

        return menu_items

    def post_init(self, t, state):
        is_default = state.active_wallet.is_default_wallet()

        if is_default:
            # Default wallet: show plain (non-editable) title, no trash button
            self.title.set_text(state.active_wallet.label)
            self._add_account_row(t, state)
            return

        # Custom wallet: editable name + trash button
        # Remove the default title label and replace with editable text area
        self.title.delete()

        self.name_textarea = title_textarea(self.title_bar)
        self.name_textarea.set_text(state.active_wallet.label)

        # Red trash button
        textarea_height = self.name_textarea.get_height()
        self.delete_btn = Btn(
            self.title_bar,
            icon=BTC_ICONS.TRASH,
            color=RED_HEX,
            size=(textarea_height, textarea_height),
        )
        self.delete_btn.align_to(self.name_textarea, lv.ALIGN.OUT_RIGHT_MID, 6, 0)

        def _on_commit(new_name):
            if self.state and self.state.active_wallet:
                self.state.active_wallet.label = new_name
                self.gui.refresh_ui()

        keyboard_binder = lambda e: self.gui.keyboard_manager.bind(self.name_textarea, Layout.FULL, _on_commit)
        self.name_textarea.add_event_cb(keyboard_binder, lv.EVENT.CLICKED, None)

        # Trash button shows delete confirmation popup
        def _on_delete(e):
            if e.get_code() != lv.EVENT.CLICKED:
                return
            wallet = self.state.active_wallet

            def _do_delete():
                self.state.remove_wallet(wallet)
                self.gui.refresh_ui()
                if hasattr(self.gui, 'ui_state') and self.gui.ui_state:
                    self.gui.ui_state.clear_history()
                    self.gui.ui_state.current_menu_id = "main"
                self.on_navigate(None)

            ActionModal(
                text=t("MODAL_DELETE_WALLET_TEXT") % wallet.label,
                buttons=[
                    (None,            t("COMMON_CANCEL"), None,    None),
                    (BTC_ICONS.TRASH, t("COMMON_DELETE"), RED_HEX, _do_delete),
                ],
            )

        self.delete_btn.add_event_cb(_on_delete, lv.EVENT.CLICKED, None)

        # Account row
        self._add_account_row(t, state)

    def _add_account_row(self, t, state):
        """Add read-only Account label row. Account is fixed at wallet creation time."""
        wallet = state.active_wallet
        if wallet is None:
            return

        row = lv.obj(self.body)
        row.set_width(lv.pct(BTN_WIDTH))
        row.set_height(BTN_HEIGHT)
        row.set_layout(lv.LAYOUT.FLEX)
        row.set_flex_flow(lv.FLEX_FLOW.ROW)
        row.set_flex_align(lv.FLEX_ALIGN.SPACE_BETWEEN, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        row.set_style_pad_hor(16, 0)
        row.set_style_radius(8, 0)
        row.set_style_border_width(0, 0)

        desc_lbl = lv.label(row)
        desc_lbl.set_text(t("WALLET_MENU_SELECT_ACCOUNT"))
        desc_lbl.set_style_text_font(lv.font_montserrat_22, 0)

        val_lbl = lv.label(row)
        val_lbl.set_style_text_font(lv.font_montserrat_22, 0)
        val_lbl.set_text(str(wallet.account))

        row.move_to_index(1)
