import lvgl as lv

from .keyboard_text_rules import accepted_chars, sanitize_text


LAYOUT_WALLET_FAVORITE = "wallet_favorite"


class KeyboardManager:
    """Shared on-screen keyboard controller for MockUI screens."""

    def __init__(self, nav_controller):
        self.nav = nav_controller
        self.keyboard = None
        self.current_layout = None
        self.active_owner = None
        self.active_textarea = None
        self.active_profile = None
        self.original_text = ""
        self.on_commit = None
        self.on_cancel = None
        self.hide_wallet_bar = False

    def open(self, owner, textarea, profile_id, on_commit=None, on_cancel=None, hide_wallet_bar=False):
        """Open keyboard for a textarea using a configured profile."""
        if self.active_owner and self.active_owner is not owner:
            self.close()

        self._ensure_keyboard()

        self.active_owner = owner
        self.active_textarea = textarea
        self.active_profile = profile_id
        self.original_text = textarea.get_text()
        self.on_commit = on_commit
        self.on_cancel = on_cancel
        self.hide_wallet_bar = bool(hide_wallet_bar)

        textarea.set_accepted_chars(accepted_chars(profile_id))
        textarea.add_state(lv.STATE.FOCUSED)

        self._apply_layout(LAYOUT_WALLET_FAVORITE)
        self.keyboard.set_textarea(textarea)
        self.keyboard.remove_flag(lv.obj.FLAG.HIDDEN)

        if self.hide_wallet_bar:
            self.nav.set_wallet_bar_visible(False)

    def close(self):
        """Hide keyboard and clear active target."""
        if self.keyboard:
            self.keyboard.add_flag(lv.obj.FLAG.HIDDEN)

        if self.hide_wallet_bar:
            self.nav.set_wallet_bar_visible(True)

        self.active_owner = None
        self.active_textarea = None
        self.active_profile = None
        self.original_text = ""
        self.on_commit = None
        self.on_cancel = None
        self.hide_wallet_bar = False

    def is_open_for(self, owner):
        return self.active_owner is owner

    def on_owner_deleted(self, owner):
        if self.active_owner is owner:
            self.close()

    def _ensure_keyboard(self):
        if self.keyboard:
            return

        self.keyboard = lv.keyboard(self.nav)
        self.keyboard.add_flag(lv.obj.FLAG.HIDDEN)
        self.keyboard.set_style_text_font(lv.font_montserrat_22, lv.PART.ITEMS)
        self.keyboard.add_event_cb(self._on_ready, lv.EVENT.READY, None)
        self.keyboard.add_event_cb(self._on_cancel_event, lv.EVENT.CANCEL, None)

    def _apply_layout(self, layout_id):
        if self.current_layout == layout_id:
            return

        map_lower, map_upper, map_special, ctrl_text, ctrl_special = self._build_wallet_favorite_layout()
        self.keyboard.set_map(lv.keyboard.MODE.TEXT_LOWER, map_lower, ctrl_text)
        self.keyboard.set_map(lv.keyboard.MODE.TEXT_UPPER, map_upper, ctrl_text)
        self.keyboard.set_map(lv.keyboard.MODE.SPECIAL, map_special, ctrl_special)
        self.current_layout = layout_id

    def _on_ready(self, e):
        if e.get_code() != lv.EVENT.READY:
            return
        if not self.active_textarea or not self.active_profile:
            return

        new_text = sanitize_text(self.active_profile, self.active_textarea.get_text())
        self.active_textarea.set_text(new_text)

        if self.on_commit:
            self.on_commit(new_text)

        self.close()

    def _on_cancel_event(self, e):
        if e.get_code() != lv.EVENT.CANCEL:
            return
        if not self.active_textarea:
            return

        self.active_textarea.set_text(self.original_text)

        if self.on_cancel:
            self.on_cancel(self.original_text)

        self.close()

    @staticmethod
    def _build_wallet_favorite_layout():
        ctrl_text = (
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 3, 1, 1, 1,
        )
        map_lower = (
            "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "\n",
            "a", "s", "d", "f", "g", "h", "j", "k", "l", "\n",
            "z", "x", "c", "v", "b", "n", "m", lv.SYMBOL.BACKSPACE, "\n",
            "ABC", "1#", " ", lv.SYMBOL.LEFT, lv.SYMBOL.RIGHT, lv.SYMBOL.OK, "",
        )
        map_upper = (
            "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "\n",
            "A", "S", "D", "F", "G", "H", "J", "K", "L", "\n",
            "Z", "X", "C", "V", "B", "N", "M", lv.SYMBOL.BACKSPACE, "\n",
            "abc", "1#", " ", lv.SYMBOL.LEFT, lv.SYMBOL.RIGHT, lv.SYMBOL.OK, "",
        )
        ctrl_special = (
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 3, 1, 1, 1,
        )
        map_special = (
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "\n",
            "!", "@", "#", "$", "%", "&", "*", "(", ")", "_", "\n",
            "-", "+", "=", "?", "/", "[", "]", "{", lv.SYMBOL.BACKSPACE, "\n",
            "ABC", "abc", " ", lv.SYMBOL.LEFT, lv.SYMBOL.RIGHT, lv.SYMBOL.OK, "",
        )
        return map_lower, map_upper, map_special, ctrl_text, ctrl_special
