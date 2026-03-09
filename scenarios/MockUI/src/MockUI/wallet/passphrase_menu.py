import lvgl as lv
from ..basic import GenericMenu, BTN_WIDTH, BTN_HEIGHT, PAD_SIZE
from ..basic.keyboard_text_rules import PROFILE_PASSPHRASE_GENERAL


class PassphraseMenu(GenericMenu):
    """Menu to enter/set the active wallet passphrase.

    menu_id: "set_passphrase"
    """

    TITLE_KEY = "MENU_SET_PASSPHRASE"

    def post_init(self, t, state):
        # Track original value for cancel/defocus
        self.original_passphrase = ""

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

        # make textarea clickable
        self.pa_ta.add_flag(lv.obj.FLAG.CLICKABLE)
        self.pa_ta.add_event_cb(self._open_keyboard, lv.EVENT.CLICKED, None)
        
        # Add defocus handler
        self.pa_ta.add_event_cb(self._on_defocus, lv.EVENT.DEFOCUSED, None)
        self.add_event_cb(lambda e: self._on_screen_delete(e), lv.EVENT.DELETE, None)

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
        self.parent.refresh_ui()

    def _open_keyboard(self, e):
        """Show keyboard for editing passphrase."""
        if e.get_code() != lv.EVENT.CLICKED:
            return
        if self.parent.keyboard_manager.is_open_for(self):
            return

        # Store original passphrase for cancel/defocus
        self.original_passphrase = self.pa_ta.get_text()

        def _on_commit(value):
            if value == "":
                self.state.active_wallet.active_passphrase = None
            else:
                self.state.active_wallet.active_passphrase = value
            self.parent.refresh_ui()
            self.on_navigate(None)

        self.parent.keyboard_manager.open(
            self,
            self.pa_ta,
            PROFILE_PASSPHRASE_GENERAL,
            on_commit=_on_commit,
            hide_wallet_bar=True,
        )

    def _on_defocus(self, e):
        """Handle text area losing focus - close keyboard and discard changes."""
        if e.get_code() != lv.EVENT.DEFOCUSED:
            return

        if self.parent.keyboard_manager.is_open_for(self):
            self.pa_ta.set_text(self.original_passphrase)
            self.parent.keyboard_manager.close()

    def _on_screen_delete(self, e):
        if e.get_code() == lv.EVENT.DELETE:
            self.parent.keyboard_manager.on_owner_deleted(self)
