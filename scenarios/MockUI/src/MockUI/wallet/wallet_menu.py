from ..basic import RED_HEX, GREEN_HEX, WHITE_HEX, GenericMenu, RED, ORANGE, TITLE_ROW_HEIGHT
from ..basic.symbol_lib import BTC_ICONS
from ..basic.keyboard_manager import Layout
from ..basic.widgets.action_modal import ActionModal
from ..basic.widgets import Btn, MenuItem, ACCEPTED_CHARS
from ..basic.widgets.labels import body_label
from ..basic.ui_consts import BTN_HEIGHT, BTN_WIDTH
import lvgl as lv


class WalletMenu(GenericMenu):
    """Menu for managing an active wallet with editable name."""

    TITLE_KEY = "MENU_MANAGE_WALLET"

    def get_menu_items(self, t, state):
        menu_items = []

        #menu_items.append(MenuItem(text=t("WALLET_MENU_MANAGE")))
        menu_items.append(MenuItem(BTC_ICONS.CONSOLE, t("WALLET_MENU_MANAGE_DESCRIPTOR"), "manage_wallet_descriptor"))
        menu_items.append(MenuItem(BTC_ICONS.BITCOIN, t("WALLET_MENU_CHANGE_NETWORK"), "change_network"))
        if (state.active_wallet and state.active_wallet.isMultiSig):
            menu_items.append(MenuItem(BTC_ICONS.ADDRESS_BOOK, t("WALLET_MENU_VIEW_SIGNERS"), "view_signers"))

        menu_items += [
            MenuItem(text=t("WALLET_MENU_CONNECT_EXPORT")),
            MenuItem(BTC_ICONS.LINK, t("MENU_CONNECT_SW_WALLET"), "connect_sw_wallet"),
            MenuItem(BTC_ICONS.EXPORT, t("WALLET_MENU_EXPORT_DATA"), "export_wallet"),
        ]

        return menu_items

    def post_init(self, t, state):
        is_default = state.active_wallet.is_default_wallet()
        if is_default:
            # Default wallet is not user-editable
            return

        # User-created wallet: editable name row at the top of the body.
        # Placing it in the body (not title_bar) ensures it is visible and
        # receives touch events — title_bar is behind the body in z-order.
        name_row = lv.obj(self.body)
        name_row.set_width(lv.pct(BTN_WIDTH))
        name_row.set_height(TITLE_ROW_HEIGHT)
        name_row.set_layout(lv.LAYOUT.FLEX)
        name_row.set_flex_flow(lv.FLEX_FLOW.ROW)
        name_row.set_flex_align(lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        name_row.set_style_pad_all(0, 0)
        name_row.set_style_pad_column(8, 0)
        name_row.set_style_border_width(0, 0)
        name_row.set_style_radius(0, 0)

        self.name_textarea = lv.textarea(name_row)
        self.name_textarea.set_width(lv.pct(85))
        self.name_textarea.set_height(TITLE_ROW_HEIGHT - 6)
        self.name_textarea.set_style_text_font(lv.font_montserrat_28, 0)
        self.name_textarea.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.name_textarea.set_style_border_width(2, lv.PART.MAIN)
        self.name_textarea.set_style_border_color(WHITE_HEX, lv.PART.MAIN)
        self.name_textarea.set_accepted_chars(ACCEPTED_CHARS)
        self.name_textarea.set_text(state.active_wallet.label)

        self.delete_btn = Btn(
            name_row,
            icon=BTC_ICONS.TRASH,
            color=RED_HEX,
            size=(TITLE_ROW_HEIGHT - 6, TITLE_ROW_HEIGHT - 6),
        )

        def _on_commit(new_name):
            if self.state and self.state.active_wallet:
                self.state.active_wallet.label = new_name
                self.gui.refresh_ui()

        keyboard_binder = lambda e: self.gui.keyboard_manager.bind(
            self.name_textarea, Layout.FULL, _on_commit
        )
        self.name_textarea.add_event_cb(keyboard_binder, lv.EVENT.CLICKED, None)

        def _on_delete(e):
            if e.get_code() != lv.EVENT.CLICKED:
                return
            wallet = self.state.active_wallet

            def _do_delete():
                self.state.remove_wallet(wallet)
                if hasattr(self.gui, 'ui_state') and self.gui.ui_state:
                    self.gui.ui_state.clear_history()
                    self.gui.ui_state.current_menu_id = "main"
                self.gui.refresh_ui()

            ActionModal(
                text=t("MODAL_DELETE_WALLET_TEXT") % wallet.label,
                buttons=[
                    (None,            t("COMMON_CANCEL"), None,    None),
                    (BTC_ICONS.TRASH, t("COMMON_DELETE"), RED_HEX, _do_delete),
                ],
            )

        self.delete_btn.add_event_cb(_on_delete, lv.EVENT.CLICKED, None)

        # Move name row to top of the flex-column body
        name_row.move_to_index(0)

        # Account row — at the start of the Manage section
        self._add_account_row(t, state)

    def _add_account_row(self, t, state):
        """Add inline Account selector (label + −/value/+ buttons) into the Manage section."""
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

        # Right side: [−] [account#] [+]
        spin_row = lv.obj(row)
        spin_row.set_height(BTN_HEIGHT - 4)
        spin_row.set_width(lv.SIZE_CONTENT)
        spin_row.set_layout(lv.LAYOUT.FLEX)
        spin_row.set_flex_flow(lv.FLEX_FLOW.ROW)
        spin_row.set_flex_align(lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        spin_row.set_style_pad_all(0, 0)
        spin_row.set_style_border_width(0, 0)
        spin_row.set_style_pad_column(4, 0)

        btn_sz = BTN_HEIGHT - 14

        dec_btn = lv.button(spin_row)
        dec_btn.set_size(btn_sz, btn_sz)
        dec_lbl = lv.label(dec_btn)
        dec_lbl.set_text(lv.SYMBOL.MINUS)
        dec_lbl.center()

        val_lbl = lv.label(spin_row)
        val_lbl.set_style_text_font(lv.font_montserrat_22, 0)
        val_lbl.set_text(str(wallet.account))
        val_lbl.set_width(50)
        val_lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)

        inc_btn = lv.button(spin_row)
        inc_btn.set_size(btn_sz, btn_sz)
        inc_lbl = lv.label(inc_btn)
        inc_lbl.set_text(lv.SYMBOL.PLUS)
        inc_lbl.center()

        def _dec_cb(e):
            if e.get_code() == lv.EVENT.CLICKED:
                if wallet.account > 0:
                    wallet.account -= 1
                    val_lbl.set_text(str(wallet.account))
                    self.gui.refresh_ui()

        def _inc_cb(e):
            if e.get_code() == lv.EVENT.CLICKED:
                if wallet.account < 99:
                    wallet.account += 1
                    val_lbl.set_text(str(wallet.account))
                    self.gui.refresh_ui()

        dec_btn.add_event_cb(_dec_cb, lv.EVENT.CLICKED, None)
        inc_btn.add_event_cb(_inc_cb, lv.EVENT.CLICKED, None)

        # Layout after post_init inserts name_row at index 0:
        #   0: name_row, 1: "Manage" header, 2: (account row here), 3: descriptor, 4: network ...
        row.move_to_index(2)
