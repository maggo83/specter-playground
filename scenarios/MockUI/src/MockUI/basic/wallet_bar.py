import lvgl as lv
from .ui_consts import BTC_ICON_WIDTH
from .symbol_lib import BTC_ICONS


class WalletBar(lv.obj):
    """Wallet status bar showing wallet-related information. Designed to be ~5% of the screen height at the bottom."""

    def __init__(self, parent, height_pct=5, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent  # for callback access

        self.set_width(lv.pct(100))
        self.set_height(lv.pct(height_pct))

        self.set_layout(lv.LAYOUT.FLEX)
        self.set_flex_flow(lv.FLEX_FLOW.ROW)
        self.set_flex_align(
            lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
        )
        self.set_style_pad_all(0, 0)
        self.set_style_radius(0, 0)
        self.set_style_border_width(0, 0)

        # Wallet name label
        self.wallet_name_lbl = lv.label(self)
        self.wallet_name_lbl.set_text("")
        self.wallet_name_lbl.set_width(100)
        self.wallet_name_lbl.set_style_text_align(lv.TEXT_ALIGN.RIGHT, 0)

        # Wallet type indicator (single/multi-sig)
        self.wallet_type_img = lv.image(self)
        self.wallet_type_img.set_width(BTC_ICON_WIDTH)

        # Passphrase indicator
        self.pp_img = lv.image(self)
        self.pp_img.set_width(BTC_ICON_WIDTH)

        # Network label
        self.net_lbl = lv.label(self)
        self.net_lbl.set_text("")
        self.net_lbl.set_width(70)

        # Apply smaller font
        self.font = lv.font_montserrat_16
        labels = [self.wallet_name_lbl, self.net_lbl]
        for lbl in labels:
            lbl.set_style_text_font(self.font, 0)

        # Make wallet-related elements clickable
        wallet_icons = [
            self.wallet_name_lbl,
            self.wallet_type_img,
            self.pp_img,
            self.net_lbl,
        ]

        for ico in wallet_icons:
            ico.add_flag(lv.obj.FLAG.CLICKABLE)
            if ico == self.wallet_name_lbl:
                ico.add_event_cb(self.wallet_name_ico_clicked, lv.EVENT.CLICKED, None)
            else:
                ico.add_event_cb(self.wallet_config_ico_clicked, lv.EVENT.CLICKED, None)

    def wallet_name_ico_clicked(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            if self.parent.specter_state.active_wallet is None:
                if self.parent.ui_state.current_menu_id != "add_wallet":
                    self.parent.show_menu("add_wallet")
            else:
                if self.parent.ui_state.current_menu_id != "change_wallet":
                    self.parent.show_menu("change_wallet")

    def wallet_config_ico_clicked(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            if self.parent.specter_state.active_wallet is None:
                if self.parent.ui_state.current_menu_id != "add_wallet":
                    self.parent.show_menu("add_wallet")
            else:
                if self.parent.ui_state.current_menu_id != "manage_wallet":
                    self.parent.show_menu("manage_wallet")

    def refresh(self, state):
        """Update visual elements from a SpecterState-like object."""
        locked = state.is_locked

        if locked:
            # Clear all content when locked (keep bar visible with same background)
            self.wallet_name_lbl.set_text("")
            self.wallet_type_img.set_src(None)
            self.pp_img.set_src(None)
            self.net_lbl.set_text("")
        else:
            # Update wallet information when unlocked
            if state.active_wallet is not None:
                w = state.active_wallet
                name = getattr(w, "name", "") or ""
                self.wallet_name_lbl.set_text(self._truncate(name, 14))
                
                # Wallet type icon
                ico = BTC_ICONS.TWO_KEYS if w.isMultiSig else BTC_ICONS.KEY
                ico.add_to_parent(self.wallet_type_img)
                
                # Passphrase indicator
                if w.active_passphrase is not None:
                    BTC_ICONS.PASSWORD.add_to_parent(self.pp_img)
                else:
                    self.pp_img.set_src(None)
                
                # Network
                self.net_lbl.set_text(self._truncate(w.net or "", 8))
            else:
                # No wallet loaded
                self.wallet_name_lbl.set_text("No wallet")
                self.wallet_type_img.set_src(None)
                self.pp_img.set_src(None)
                self.net_lbl.set_text("")

    def _truncate(self, text, max_chars):
        """Return text truncated to max_chars."""
        if not text:
            return ""
        s = str(text)
        if len(s) <= max_chars:
            return s
        if max_chars <= 3:
            return s[:3]
        return s[:max_chars]
