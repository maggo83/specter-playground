import lvgl as lv
from ..helpers import Battery
from .ui_consts import BTC_ICON_WIDTH, GREEN_HEX, ORANGE_HEX, RED_HEX, STATUS_BTN_HEIGHT, STATUS_BTN_WIDTH, THREE_LETTER_SYMBOL_WIDTH
from .symbol_lib import BTC_ICONS


class DeviceBar(lv.obj):
    """Device status bar showing system-level information. Designed to be ~5% of the screen height at the top."""

    def __init__(self, parent, height_pct=5, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent  # for callback access

        self.set_width(lv.pct(100))
        self.set_height(lv.pct(height_pct))

        self.set_layout(lv.LAYOUT.FLEX)
        self.set_flex_flow(lv.FLEX_FLOW.ROW)
        self.set_flex_align(
            lv.FLEX_ALIGN.SPACE_BETWEEN, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
        )
        self.set_style_pad_all(0, 0)
        self.set_style_radius(0, 0)
        self.set_style_border_width(0, 0)

        # LEFT SECTION: Lock button
        self.left_container = lv.obj(self)
        self.left_container.set_width(STATUS_BTN_WIDTH + 10)
        self.left_container.set_height(lv.pct(100))
        self.left_container.set_layout(lv.LAYOUT.FLEX)
        self.left_container.set_flex_flow(lv.FLEX_FLOW.ROW)
        self.left_container.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        self.left_container.set_style_pad_all(0, 0)
        self.left_container.set_style_border_width(0, 0)

        self.lock_btn = lv.button(self.left_container)
        self.lock_btn.set_size(STATUS_BTN_WIDTH, STATUS_BTN_HEIGHT)
        self.lock_ico = lv.image(self.lock_btn)
        BTC_ICONS.UNLOCK.add_to_parent(self.lock_ico)
        self.lock_ico.center()
        self.lock_btn.add_event_cb(self.lock_cb, lv.EVENT.CLICKED, None)

        # CENTER SECTION: Peripheral indicators
        self.center_container = lv.obj(self)
        self.center_container.set_width(BTC_ICON_WIDTH * 4 + 40)
        self.center_container.set_height(lv.pct(100))
        self.center_container.set_layout(lv.LAYOUT.FLEX)
        self.center_container.set_flex_flow(lv.FLEX_FLOW.ROW)
        self.center_container.set_flex_align(lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        self.center_container.set_style_pad_all(0, 0)
        self.center_container.set_style_border_width(0, 0)

        # Peripheral indicators (only visible when unlocked)
        self.qr_img = lv.image(self.center_container)
        self.qr_img.set_width(BTC_ICON_WIDTH)

        self.usb_img = lv.image(self.center_container)
        self.usb_img.set_width(BTC_ICON_WIDTH)

        self.sd_img = lv.image(self.center_container)
        self.sd_img.set_width(BTC_ICON_WIDTH)

        self.smartcard_img = lv.image(self.center_container)
        self.smartcard_img.set_width(BTC_ICON_WIDTH)

        # Make peripheral icons clickable to navigate to interfaces menu
        peripheral_icons = [
            self.qr_img,
            self.usb_img,
            self.sd_img,
            self.smartcard_img,
        ]
        for ico in peripheral_icons:
            ico.add_flag(lv.obj.FLAG.CLICKABLE)
            ico.add_event_cb(self.peripheral_ico_clicked, lv.EVENT.CLICKED, None)

        # RIGHT SECTION: Battery, Language, Settings, Power (in that order)
        self.right_container = lv.obj(self)
        self.right_container.set_width(STATUS_BTN_WIDTH * 2 + THREE_LETTER_SYMBOL_WIDTH + 70)
        self.right_container.set_height(lv.pct(100))
        self.right_container.set_layout(lv.LAYOUT.FLEX)
        self.right_container.set_flex_flow(lv.FLEX_FLOW.ROW)
        self.right_container.set_flex_align(lv.FLEX_ALIGN.END, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        self.right_container.set_style_pad_all(0, 0)
        self.right_container.set_style_border_width(0, 0)

        # Battery icon
        self.batt_icon = Battery(self.right_container)
        self.batt_icon.VALUE = parent.specter_state.battery_pct
        self.batt_icon.update()

        # Language indicator (clickable selector) - always visible
        self.lang_lbl = lv.label(self.right_container)
        self.lang_lbl.set_text("")
        self.lang_lbl.set_width(THREE_LETTER_SYMBOL_WIDTH)
        self.lang_lbl.add_flag(lv.obj.FLAG.CLICKABLE)
        self.lang_lbl.add_event_cb(self.lang_clicked, lv.EVENT.CLICKED, None)

        # Settings button
        self.settings_btn = lv.button(self.right_container)
        self.settings_btn.set_size(STATUS_BTN_WIDTH, STATUS_BTN_HEIGHT)
        self.settings_ico = lv.image(self.settings_btn)
        BTC_ICONS.GEAR.add_to_parent(self.settings_ico)
        self.settings_ico.center()
        self.settings_btn.add_event_cb(self.settings_cb, lv.EVENT.CLICKED, None)

        # Power button
        self.power_btn = lv.button(self.right_container)
        self.power_btn.set_size(STATUS_BTN_WIDTH, STATUS_BTN_HEIGHT)
        self.power_lbl = lv.label(self.power_btn)
        self.power_lbl.set_text(lv.SYMBOL.POWER)
        self.power_lbl.center()
        self.power_btn.add_event_cb(self.power_cb, lv.EVENT.CLICKED, None)

        # Apply smaller font to labels
        self.font = lv.font_montserrat_12
        labels = [self.lang_lbl, self.power_lbl]
        for lbl in labels:
            lbl.set_style_text_font(self.font, 0)

    def power_cb(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            if self.parent.specter_state.battery_pct is None:
                self.parent.specter_state.battery_pct = 50
                self.parent.refresh_ui()
            else:
                self.parent.specter_state.battery_pct = None
                self.parent.refresh_ui()

    def lock_cb(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            if self.parent.specter_state.is_locked:
                # unlocking should be handled by the locked screen's PIN flow
                return
            else:
                # lock the device and force NavigationController to show the locked screen
                self.parent.specter_state.lock()
                # show_menu will detect is_locked and show the locked screen
                self.parent.show_menu(None)

    def peripheral_ico_clicked(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            if self.parent.ui_state.current_menu_id != "interfaces":
                self.parent.show_menu("interfaces")

    def lang_clicked(self, e):
        """Navigate to language selection menu when language label is clicked."""
        if e.get_code() == lv.EVENT.CLICKED:
            if self.parent.ui_state.current_menu_id != "select_language":
                self.parent.show_menu("select_language")

    def settings_cb(self, e):
        """Navigate to settings menu when settings button is clicked."""
        if e.get_code() == lv.EVENT.CLICKED:
            if self.parent.ui_state.current_menu_id != "manage_settings":
                self.parent.show_menu("manage_settings")

    def refresh(self, state):
        """Update visual elements from a SpecterState-like object."""
        locked = state.is_locked

        # Battery (always visible)
        self.batt_icon.CHARGING = state.is_charging
        if state.has_battery:
            perc = state.battery_pct
            self.batt_icon.VALUE = perc
            self.batt_icon.update()
        else:
            self.batt_icon.VALUE = 100
            self.batt_icon.update()

        # Language (always visible)
        lang_code = self.parent.i18n.get_language()
        self.lang_lbl.set_text(self._truncate(lang_code.upper(), 3))

        # Lock icon (always visible, but changes based on state)
        if locked:
            BTC_ICONS.LOCK.add_to_parent(self.lock_ico)
            # Hide peripheral indicators when locked
            self.qr_img.set_src(None)
            self.usb_img.set_src(None)
            self.sd_img.set_src(None)
            self.smartcard_img.set_src(None)
        else:
            BTC_ICONS.UNLOCK.add_to_parent(self.lock_ico)
            # Show peripheral indicators when unlocked
            if state.hasQR:
                if state.enabledQR:
                    BTC_ICONS.QR_CODE(GREEN_HEX).add_to_parent(self.qr_img)
                else:
                    BTC_ICONS.QR_CODE(ORANGE_HEX).add_to_parent(self.qr_img)
            else:
                self.qr_img.set_src(None)

            if state.hasUSB:
                if state.enabledUSB:
                    BTC_ICONS.USB(GREEN_HEX).add_to_parent(self.usb_img)
                else:
                    BTC_ICONS.USB(ORANGE_HEX).add_to_parent(self.usb_img)
            else:
                self.usb_img.set_src(None)

            if state.hasSD:
                if state.enabledSD:
                    if state.detectedSD:
                        BTC_ICONS.SD_CARD(GREEN_HEX).add_to_parent(self.sd_img)
                    else:
                        BTC_ICONS.SD_CARD(ORANGE_HEX).add_to_parent(self.sd_img)
                else:
                    BTC_ICONS.SD_CARD(RED_HEX).add_to_parent(self.sd_img)
            else:
                self.sd_img.set_src(None)

            if state.hasSmartCard:
                if state.enabledSmartCard:
                    if state.detectedSmartCard:
                        BTC_ICONS.SMARTCARD(GREEN_HEX).add_to_parent(self.smartcard_img)
                    else:
                        BTC_ICONS.SMARTCARD(ORANGE_HEX).add_to_parent(self.smartcard_img)
                else:
                    BTC_ICONS.SMARTCARD(RED_HEX).add_to_parent(self.smartcard_img)
            else:
                self.smartcard_img.set_src(None)

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
