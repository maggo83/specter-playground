from ..basic import GREY_HEX, ORANGE_HEX, RED_HEX, WHITE_HEX, GenericMenu, TITLE_ROW_HEIGHT, BTC_ICON_WIDTH
from ..basic.symbol_lib import BTC_ICONS
from ..basic.keyboard_manager import Layout
from ..basic.widgets.action_modal import ActionModal
from ..basic.widgets import Btn, MenuItem, ACCEPTED_CHARS
from ..basic.ui_consts import BTN_HEIGHT, BTN_WIDTH
import lvgl as lv

class SeedPhraseMenu(GenericMenu):
    """Manage Seedphrase menu — includes passphrase, storage, and advanced options.

    menu_id: "manage_seedphrase"
    """
    TITLE_KEY = "MENU_MANAGE_SEED"

    def get_menu_items(self, t, state):
        menu_items = []

        menu_items.append(MenuItem(BTC_ICONS.VISIBLE, t("SEEDPHRASE_MENU_SHOW"), "show_seedphrase", color=ORANGE_HEX))

        pp_label = t("MENU_CHANGE_CLEAR_PASSPHRASE") if state.active_seed.passphrase else t("MENU_SET_PASSPHRASE")
        menu_items.append(MenuItem(BTC_ICONS.PASSWORD, pp_label, "set_passphrase"))

        menu_items.append(MenuItem(text=t("SEEDPHRASE_MENU_STORAGE")))
        menu_items.append(MenuItem(lv.SYMBOL.DOWNLOAD, t("SEEDPHRASE_MENU_STORE_TO") + "...", "store_seedphrase"))
        menu_items.append(MenuItem(BTC_ICONS.TRASH, t("SEEDPHRASE_MENU_CLEAR_FROM") + "...", "clear_seedphrase", color=RED_HEX))

        menu_items.append(MenuItem(text=t("SEEDPHRASE_MENU_ADVANCED")))
        menu_items.append(MenuItem(BTC_ICONS.SHARED_WALLET, t("SEEDPHRASE_MENU_BIP85"), "derive_bip85"))

        return menu_items

    def post_init(self, t, state):
        # Editable seed name row at the top of the body.
        # Placed in the body (not title_bar) so it is visible and receives events
        # — title_bar is behind the body in z-order and unreachable.
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
        # narrower when fp will be shown alongside (single seed loaded)
        ta_width = lv.pct(60) if len(state.loaded_seeds) <= 1 else lv.pct(85)
        self.name_textarea.set_width(ta_width)
        self.name_textarea.set_height(TITLE_ROW_HEIGHT - 6)
        self.name_textarea.set_style_text_font(lv.font_montserrat_28, 0)
        self.name_textarea.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.name_textarea.set_style_border_width(2, lv.PART.MAIN)
        self.name_textarea.set_style_border_color(WHITE_HEX, lv.PART.MAIN)
        self.name_textarea.set_accepted_chars(ACCEPTED_CHARS)
        self.name_textarea.set_text(state.active_seed.label)

        # Fingerprint only when seed bar hides it (single seed loaded)
        if len(state.loaded_seeds) <= 1:
            raw_fp = state.active_seed.fingerprint if state.active_seed.fingerprint else "????"
            if raw_fp.startswith("0x") or raw_fp.startswith("0X"):
                raw_fp = raw_fp[2:]
            fp_img = lv.image(name_row)
            fp_img.set_width(BTC_ICON_WIDTH)
            BTC_ICONS.RELAY(GREY_HEX).add_to_parent(fp_img)
            fp_lbl = lv.label(name_row)
            fp_lbl.set_text(raw_fp[:4])
            fp_lbl.set_style_text_font(lv.font_montserrat_16, 0)
            fp_lbl.set_width(lv.SIZE_CONTENT)

        self.delete_btn = Btn(
            name_row,
            icon=BTC_ICONS.TRASH,
            color=RED_HEX,
            size=(TITLE_ROW_HEIGHT - 6, TITLE_ROW_HEIGHT - 6),
        )

        def _on_commit(new_name):
            state.active_seed.label = new_name
            self.gui.refresh_ui()

        keyboard_binder = lambda e: self.gui.keyboard_manager.bind(
            self.name_textarea, Layout.FULL, _on_commit
        )
        self.name_textarea.add_event_cb(keyboard_binder, lv.EVENT.CLICKED, None)

        def _on_delete(e):
            if e.get_code() != lv.EVENT.CLICKED:
                return
            seed = self.state.active_seed

            def _do_delete():
                self.state.remove_seed(seed)
                if hasattr(self.gui, 'ui_state') and self.gui.ui_state:
                    self.gui.ui_state.clear_history()
                    self.gui.ui_state.current_menu_id = "main"
                self.gui.refresh_ui()

            ActionModal(
                text=t("MODAL_DELETE_SEED_TEXT") % seed.label,
                buttons=[
                    (None,            t("COMMON_CANCEL"), None,    None),
                    (BTC_ICONS.TRASH, t("COMMON_DELETE"), RED_HEX, _do_delete),
                ],
            )

        self.delete_btn.add_event_cb(_on_delete, lv.EVENT.CLICKED, None)

        # Move name row to top of the flex-column body
        name_row.move_to_index(0)
