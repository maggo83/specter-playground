from ..basic import RED_HEX, WHITE_HEX, GenericMenu, RED, ORANGE, TITLE_ROW_HEIGHT
from ..basic.symbol_lib import BTC_ICONS
from ..basic.keyboard_manager import Layout
from ..basic.modal_overlay import ModalOverlay
import lvgl as lv


class WalletMenu(GenericMenu):
    """Menu for managing an active wallet with editable name."""

    TITLE_KEY = "MENU_MANAGE_WALLET"

    def get_menu_items(self, t, state):
        menu_items = []

        menu_items.append((None, t("WALLET_MENU_EXPLORE"), None, None, None, None))
        menu_items.append((BTC_ICONS.MENU, t("WALLET_MENU_VIEW_ADDRESSES"), "view_addresses", None, None, None))
        if (state.active_wallet and state.active_wallet.isMultiSig):
            menu_items.append((BTC_ICONS.ADDRESS_BOOK, t("WALLET_MENU_VIEW_SIGNERS"), "view_signers", None, None, None))

        menu_items.append((None, t("WALLET_MENU_MANAGE"), None, None, None, None))
        menu_items.append((BTC_ICONS.CONSOLE, t("WALLET_MENU_MANAGE_DESCRIPTOR"), "manage_wallet_descriptor", None, None, None))
        menu_items.append((BTC_ICONS.BITCOIN, t("WALLET_MENU_CHANGE_NETWORK"), "change_network", None, None, None))

        menu_items += [
            (None, t("WALLET_MENU_CONNECT_EXPORT"), None, None, None, None),
            (BTC_ICONS.LINK, t("MENU_CONNECT_SW_WALLET"), "connect_sw_wallet", None, None, None),
            (BTC_ICONS.EXPORT, t("WALLET_MENU_EXPORT_DATA"), "export_wallet", None, None, None)
        ]

        return menu_items

    def post_init(self, t, state):
        is_default = state.active_wallet.is_default_wallet()

        if is_default:
            # Default Wallet: show plain (non-editable) title, no trash button
            self.title.set_text(state.active_wallet.label)
        else:
            # Custom wallet: editable name + trash button
            # Remove the default title label and replace with editable text area
            self.title.delete()

            self.name_textarea = lv.textarea(self.title_bar)
            self.name_textarea.set_width(270)
            self.name_textarea.set_height(TITLE_ROW_HEIGHT)
            self.name_textarea.set_style_text_font(lv.font_montserrat_28, 0)
            self.name_textarea.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
            self.name_textarea.set_style_border_width(2, lv.PART.MAIN)
            self.name_textarea.set_style_border_color(WHITE_HEX, lv.PART.MAIN)
            self.name_textarea.align(lv.ALIGN.CENTER, 0, 0)
            self.name_textarea.set_accepted_chars("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/~ ")

            self.name_textarea.set_text(state.active_wallet.label)

            # Red trash button
            textarea_height = self.name_textarea.get_height()
            self.delete_btn = lv.button(self.title_bar)
            self.delete_btn.set_size(textarea_height, textarea_height)
            self.delete_btn.set_style_bg_color(RED_HEX, lv.PART.MAIN)
            self.delete_ico = lv.image(self.delete_btn)
            BTC_ICONS.TRASH.add_to_parent(self.delete_ico)
            self.delete_ico.center()
            self.delete_btn.align_to(self.name_textarea, lv.ALIGN.OUT_RIGHT_MID, 6, 0)

            def _on_commit(new_name):
                if self.state and self.state.active_wallet:
                    self.state.active_wallet.label = new_name
                    self.gui.refresh_ui()

            keyboard_binder = lambda e: self.gui.keyboard_manager.bind(self.name_textarea, Layout.FULL, _on_commit)
            self.name_textarea.add_event_cb(keyboard_binder, lv.EVENT.CLICKED, None)

        if is_default:
            # No delete button for default wallet, skip rest of post_init
            return

        # Trash button shows delete confirmation popup
        def _on_delete(e):
            if e.get_code() != lv.EVENT.CLICKED:
                return
            
            wallet = self.state.active_wallet

            modal = ModalOverlay(bg_opa=180)
            sw = modal.screen_width
            sh = modal.screen_height

            dw = sw * 80 // 100
            dh = sh * 40 // 100
            dx = (sw - dw) // 2
            dy = (sh - dh) // 2

            dialog = lv.obj(modal.overlay)
            dialog.set_size(dw, dh)
            dialog.set_pos(dx, dy)
            dialog.set_style_radius(8, 0)
            dialog.set_style_border_width(0, 0)
            dialog.set_style_pad_all(12, 0)
            dialog.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
            dialog.set_layout(lv.LAYOUT.FLEX)
            dialog.set_flex_flow(lv.FLEX_FLOW.COLUMN)
            dialog.set_flex_align(lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

            warn_lbl = lv.label(dialog)
            warn_lbl.set_text("Delete wallet \"%s\"?\nThis cannot be undone." % wallet.label)
            warn_lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
            warn_lbl.set_style_text_font(lv.font_montserrat_22, 0)
            warn_lbl.set_width(lv.pct(100))
            warn_lbl.set_long_mode(lv.label.LONG_MODE.WRAP)

            # Button row
            btn_row = lv.obj(dialog)
            btn_row.set_width(lv.pct(100))
            btn_row.set_height(60)
            btn_row.set_layout(lv.LAYOUT.FLEX)
            btn_row.set_flex_flow(lv.FLEX_FLOW.ROW)
            btn_row.set_flex_align(lv.FLEX_ALIGN.SPACE_EVENLY, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
            btn_row.set_style_border_width(0, 0)
            btn_row.set_style_pad_all(0, 0)

            cancel_btn = lv.button(btn_row)
            cancel_lbl = lv.label(cancel_btn)
            cancel_lbl.set_text("Cancel")
            cancel_lbl.set_style_text_font(lv.font_montserrat_22, 0)
            cancel_lbl.center()

            del_btn = lv.button(btn_row)
            del_btn.set_style_bg_color(RED_HEX, lv.PART.MAIN)
            del_lbl = lv.label(del_btn)
            del_lbl.set_text("Delete")
            del_lbl.set_style_text_font(lv.font_montserrat_22, 0)
            del_lbl.center()

            def _cancel(ev):
                if ev.get_code() == lv.EVENT.CLICKED:
                    modal.close()

            def _confirm_delete(ev):
                if ev.get_code() == lv.EVENT.CLICKED:
                    modal.close()
                    self.state.remove_wallet(wallet)
                    self.gui.refresh_ui()
                    if hasattr(self.gui, 'ui_state') and self.gui.ui_state:
                        self.gui.ui_state.clear_history()
                        self.gui.ui_state.current_menu_id = "main"
                    self.on_navigate(None)

            cancel_btn.add_event_cb(_cancel, lv.EVENT.CLICKED, None)
            del_btn.add_event_cb(_confirm_delete, lv.EVENT.CLICKED, None)

        self.delete_btn.add_event_cb(_on_delete, lv.EVENT.CLICKED, None)
