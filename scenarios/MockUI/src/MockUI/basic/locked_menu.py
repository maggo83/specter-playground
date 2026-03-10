import lvgl as lv
from .titled_screen import TitledScreen
from .symbol_lib import BTC_ICONS
from .ui_consts import PIN_BTN_WIDTH, PIN_BTN_HEIGHT


class LockedMenu(TitledScreen):
    """Simple lock screen that accepts a numeric PIN to unlock the device."""

    def __init__(self, parent):
        super().__init__(parent.i18n.t("LOCKED_MENU_TITLE"), parent)

        self.pin_buf = ""
        t = parent.i18n.t

        self.body.set_layout(lv.LAYOUT.FLEX)
        self.body.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.body.set_flex_align(
            lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
        )

        # Firmware version – shown as a subtitle directly under the title bar,
        # inside the TITLE_PADDING gap so it doesn't push body content down.
        fw_ver = lv.label(self)
        fw_ver.set_text(t("LOCKED_MENU_FW_VERSION") + str(self.state.fw_version))
        fw_ver.set_width(lv.pct(100))
        fw_ver.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        fw_ver.set_style_text_font(lv.font_montserrat_16, 0)
        fw_ver.align_to(self.title_bar, lv.ALIGN.OUT_BOTTOM_MID, 0, 1)

        # Instruction label
        instr = lv.label(self.body)
        instr.set_text(t("LOCKED_MENU_ENTER_PIN"))
        instr.set_width(320)
        instr.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        instr.set_style_text_font(lv.font_montserrat_28, 0)

        # masked PIN display
        self.mask_lbl = lv.label(self.body)
        self.mask_lbl.set_text("")
        self.mask_lbl.set_width(320)
        self.mask_lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.mask_lbl.set_style_text_font(lv.font_montserrat_28, 0)

        # keypad layout (3x4): 1..9, Del, 0, OK
        keys = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["Del", "0", "OK"],
        ]

        for row in keys:
            row_cont = lv.obj(self.body)
            # make the row container slightly taller than the buttons so they fit
            row_cont.set_layout(lv.LAYOUT.FLEX)
            row_cont.set_flex_flow(lv.FLEX_FLOW.ROW)
            row_cont.set_width(lv.pct(100))
            row_cont.set_height(lv.SIZE_CONTENT)
            # center buttons in the row and remove visible backgrounds/borders
            row_cont.set_flex_align(
                lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
            )
            row_cont.set_style_border_width(0, 0)
            row_cont.set_style_pad_all(0, 0)

            for k in row:
                b = lv.button(row_cont)
                b.set_width(PIN_BTN_WIDTH)
                b.set_height(PIN_BTN_HEIGHT)
                if k == "Del":
                    im = lv.image(b)
                    BTC_ICONS.CLEAR_CHARACTER.add_to_parent(im)
                    im.center()
                    b.add_event_cb(lambda e: self._on_del(e), lv.EVENT.CLICKED, None)
                elif k == "OK":
                    im = lv.image(b)
                    BTC_ICONS.CHECK.add_to_parent(im)
                    im.center()
                    b.add_event_cb(lambda e: self._on_ok(e), lv.EVENT.CLICKED, None)
                else:
                    # capture digit in default arg
                    lb = lv.label(b)
                    lb.center()
                    lb.set_text(k)
                    lb.set_style_text_font(lv.font_montserrat_22, 0)
                    b.add_event_cb(lambda e, d=k: self._on_digit(e, d), lv.EVENT.CLICKED, None)

    def _update_mask(self):
        self.mask_lbl.set_text("*" * len(self.pin_buf))

    def _on_digit(self, e, d):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        # append up to 8 digits
        if len(self.pin_buf) >= 8:
            return
        self.pin_buf += d
        self._update_mask()

    def _on_del(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        if not self.pin_buf:
            return
        self.pin_buf = self.pin_buf[:-1]
        self._update_mask()

    def _on_ok(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        pin = self.pin_buf
        # attempt unlock; SpecterState.unlock will check PIN
        unlocked = self.state.unlock(pin)
        if unlocked:
            # reset UI history and show main menu
            self.gui.ui_state.clear_history()
            # Ensure state updated
            self.state.is_locked = False
            # load main menu fresh
            self.gui.ui_state.current_menu_id = "main"
            # delete current and create main menu
            if self.gui.current_screen:
                self.gui.current_screen.delete()
            self.gui.current_screen = None
            self.on_navigate(None)
        else:
            # clear buffer and indicate failure (simple UX)
            self.pin_buf = ""
            self._update_mask()
