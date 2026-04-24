from ..basic import ORANGE_HEX, RED_HEX, WHITE_HEX, GenericMenu, TITLE_ROW_HEIGHT
from ..basic.symbol_lib import BTC_ICONS
from ..basic.keyboard_manager import Layout
from ..basic.modal_overlay import ModalOverlay
import lvgl as lv

class SeedPhraseMenu(GenericMenu):
    """Manage Seedphrase menu — includes passphrase, storage, and advanced options.

    menu_id: "manage_seedphrase"
    """
    TITLE_KEY = "MENU_MANAGE_SEED"

    def get_menu_items(self, t, state):
        menu_items = []

        # Show the seedphrase (requires confirmation on a real device)
        menu_items.append((BTC_ICONS.VISIBLE, t("SEEDPHRASE_MENU_SHOW"), "show_seedphrase", ORANGE_HEX, None, None))

        # Passphrase
        pp_label = ""
        if state.active_seed.passphrase:
            pp_label = t("MENU_CHANGE_CLEAR_PASSPHRASE")
        else:
            pp_label = t("MENU_SET_PASSPHRASE")
        menu_items.append((BTC_ICONS.PASSWORD, pp_label, "set_passphrase", None, None, None))

        # Storage sub-menus
        menu_items.append((None, t("SEEDPHRASE_MENU_STORAGE"), None, None, None, None))
        menu_items.append((lv.SYMBOL.DOWNLOAD, t("SEEDPHRASE_MENU_STORE_TO") + "...", "store_seedphrase", None, None, None))
        menu_items.append((BTC_ICONS.TRASH, t("SEEDPHRASE_MENU_CLEAR_FROM") + "...", "clear_seedphrase", RED_HEX, None, None))

        # Derive new via BIP-85
        menu_items.append((None, t("SEEDPHRASE_MENU_ADVANCED"), None, None, None, None))
        menu_items.append((BTC_ICONS.SHARED_WALLET, t("SEEDPHRASE_MENU_BIP85"), "derive_bip85", None, None, None))

        return menu_items

    def post_init(self, t, state):
        # Replace the default title label with editable text area + delete button
        # (same pattern as WalletMenu)
        self.title.delete()

        # Text area for seed name (editable) – lives in title_bar, centred
        self.name_textarea = lv.textarea(self.title_bar)
        self.name_textarea.set_width(270)
        self.name_textarea.set_height(TITLE_ROW_HEIGHT)
        self.name_textarea.set_style_text_font(lv.font_montserrat_28, 0)
        self.name_textarea.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.name_textarea.set_style_border_width(2, lv.PART.MAIN)
        self.name_textarea.set_style_border_color(WHITE_HEX, lv.PART.MAIN)
        self.name_textarea.align(lv.ALIGN.CENTER, 0, 0)
        self.name_textarea.set_accepted_chars(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/~ "
        )

        # Set initial text from active seed
        self.name_textarea.set_text(state.active_seed.label)

        # Red trash button – square, matching textarea height
        textarea_height = self.name_textarea.get_height()
        self.delete_btn = lv.button(self.title_bar)
        self.delete_btn.set_size(textarea_height, textarea_height)
        self.delete_btn.set_style_bg_color(RED_HEX, lv.PART.MAIN)
        self.delete_ico = lv.image(self.delete_btn)
        BTC_ICONS.TRASH.add_to_parent(self.delete_ico)
        self.delete_ico.center()
        self.delete_btn.align_to(self.name_textarea, lv.ALIGN.OUT_RIGHT_MID, 6, 0)

        def _on_commit(new_name):
            state.active_seed.label = new_name
            self.gui.refresh_ui()

        keyboard_binder = lambda e: self.gui.keyboard_manager.bind(
            self.name_textarea, Layout.FULL, _on_commit
        )
        self.name_textarea.add_event_cb(keyboard_binder, lv.EVENT.CLICKED, None)

        # Trash button shows delete confirmation popup
        def _on_delete(e):
            if e.get_code() != lv.EVENT.CLICKED:
                return
            seed = self.state.active_seed

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
            warn_lbl.set_text("Delete seed \"%s\"?\nThis will remove the key from memory." % seed.label)
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
                    self.state.remove_seed(seed)
                    self.gui.refresh_ui()
                    if hasattr(self.gui, 'ui_state') and self.gui.ui_state:
                        self.gui.ui_state.clear_history()
                        self.gui.ui_state.current_menu_id = "main"
                    self.on_navigate(None)

            cancel_btn.add_event_cb(_cancel, lv.EVENT.CLICKED, None)
            del_btn.add_event_cb(_confirm_delete, lv.EVENT.CLICKED, None)

        self.delete_btn.add_event_cb(_on_delete, lv.EVENT.CLICKED, None)
