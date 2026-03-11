import lvgl as lv
from ..basic import TitledScreen, BTN_WIDTH, BTN_HEIGHT, PAD_SIZE
from ..basic.keyboard_manager import Layout

def _sanitize_passphrase(text):
    return text.strip()


class PassphraseMenu(TitledScreen):
    """Form to enter/set the active wallet passphrase.

    menu_id: "set_passphrase"
    """

    def __init__(self, parent):
        super().__init__(parent.i18n.t("MENU_SET_PASSPHRASE"), parent)
        t = self.i18n.t

        self.body.set_layout(lv.LAYOUT.FLEX)
        self.body.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.body.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        # Row for passphrase input
        pa_row = lv.obj(self.body)
        pa_row.set_width(lv.pct(100))
        pa_row.set_height(lv.pct(20))
        pa_row.set_layout(lv.LAYOUT.FLEX)
        pa_row.set_flex_flow(lv.FLEX_FLOW.ROW)
        pa_row.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        pa_row.set_style_border_width(0, 0)

        pa_lbl = lv.label(pa_row)
        pa_lbl.set_text(t("PASSPHRASE_MENU_LABEL"))
        pa_lbl.set_width(lv.pct(30))
        pa_lbl.set_style_text_align(lv.TEXT_ALIGN.LEFT, 0)
        pa_lbl.set_style_text_font(lv.font_montserrat_22, 0)

        # editable textarea
        self.pa_ta = lv.textarea(pa_row)
        # prefill with active passphrase (might be empty)
        val = ""
        if self.state.active_wallet.active_passphrase is not None:
            val = self.state.active_wallet.active_passphrase
        self.pa_ta.set_text(val)
        self.pa_ta.set_width(lv.pct(60))
        self.pa_ta.set_height(50)
        self.pa_ta.set_style_text_font(lv.font_montserrat_22, 0)
        self.pa_ta.set_accepted_chars("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/~ ")  # No newlines

        def _on_commit(value):
            if not value:
                self.state.active_wallet.active_passphrase = None
            else:
                self.state.active_wallet.active_passphrase = value
            self.gui.refresh_ui()
            self.on_navigate(None)

        keyboard_binder = lambda e: self.gui.keyboard_manager.bind(self.pa_ta, Layout.FULL, _on_commit, _sanitize_passphrase)
        self.pa_ta.add_event_cb(keyboard_binder, lv.EVENT.CLICKED, None)

        buttons_row = lv.obj(self.body)
        buttons_row.set_width(lv.pct(100))
        buttons_row.set_height(lv.pct(50))
        buttons_row.set_layout(lv.LAYOUT.FLEX)
        buttons_row.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        buttons_row.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        buttons_row.set_style_pad_all(PAD_SIZE, 0)
        buttons_row.set_style_border_width(0, 0)

        # Clear button
        self.clear_btn = lv.button(buttons_row)
        self.clear_btn.set_width(lv.pct(BTN_WIDTH))
        self.clear_btn.set_height(BTN_HEIGHT)
        self.clear_lbl = lv.label(self.clear_btn)
        self.clear_lbl.set_text(lv.SYMBOL.CLOSE + " " + t("PASSPHRASE_MENU_CLEAR"))
        self.clear_lbl.set_style_text_font(lv.font_montserrat_22, 0)
        self.clear_lbl.center()
        self.clear_btn.add_event_cb(self._on_clear, lv.EVENT.CLICKED, None)

    def _on_clear(self, e):
        """Clear passphrase and update state."""
        if e.get_code() != lv.EVENT.CLICKED:
            return
        
        # Clear text area
        self.pa_ta.set_text("")
        # Clear passphrase in state
        self.state.active_wallet.active_passphrase = None
        # Refresh UI
        self.gui.refresh_ui()
