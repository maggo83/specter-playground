import lvgl as lv
from ..stubs import Battery
from .ui_consts import BTC_ICON_WIDTH, GREEN_HEX, WHITE_HEX, GREY_HEX, STATUS_BTN_HEIGHT, STATUS_BTN_WIDTH
from .symbol_lib import BTC_ICONS
from .widgets.btn import Btn
from .widgets.containers import flex_row


class DeviceBar(lv.obj):
    """Device status bar showing system-level information. Designed to be ~5% of the screen height at the top."""

    def __init__(self, gui, height_pct=5):
        super().__init__(gui)

        self.gui = gui  # for callback access

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
        self.left_container = flex_row(
            self, width=STATUS_BTN_WIDTH, height=lv.pct(100),
            main_align=lv.FLEX_ALIGN.START,
        )
        self.lock_btn = Btn(
            self.left_container,
            icon=BTC_ICONS.UNLOCK,
            size=(STATUS_BTN_WIDTH, STATUS_BTN_HEIGHT),
            callback=self.lock_cb,
        )

        # CENTER SECTION: Peripheral indicators
        self.center_container = flex_row(
            self, width=BTC_ICON_WIDTH * 4 + 30, height=lv.pct(100),
            main_align=lv.FLEX_ALIGN.CENTER,
        )

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

        # RIGHT SECTION: Battery, Settings, Power (in that order)
        self.right_container = flex_row(
            self, width=STATUS_BTN_WIDTH * 3, height=lv.pct(100),
            main_align=lv.FLEX_ALIGN.END,
        )

        # Battery icon
        self.batt_icon = Battery(self.right_container)
        self.batt_icon.VALUE = gui.specter_state.battery_pct
        self.batt_icon.update()

        # Settings button
        self.settings_btn = Btn(
            self.right_container,
            icon=BTC_ICONS.GEAR,
            size=(STATUS_BTN_WIDTH, STATUS_BTN_HEIGHT),
            callback=self.settings_cb,
        )

        # Power button (uses lv.SYMBOL string, not a custom Icon)
        self.power_btn = Btn(
            self.right_container,
            text=lv.SYMBOL.POWER,
            size=(STATUS_BTN_WIDTH, STATUS_BTN_HEIGHT),
            font=lv.font_montserrat_16,
            callback=self.power_cb,
        )

    def power_cb(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            if self.gui.specter_state.battery_pct is None:
                self.gui.specter_state.battery_pct = 50
                self.gui.refresh_ui()
            else:
                self.gui.specter_state.battery_pct = None
                self.gui.refresh_ui()

    def lock_cb(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            if self.gui.specter_state.is_locked:
                # unlocking should be handled by the locked screen's PIN flow
                return
            else:
                # lock the device and force SpecterGui to show the locked screen
                self.gui.specter_state.lock()
                # show_menu will detect is_locked and show the locked screen
                self.gui.show_menu(None)

    def peripheral_ico_clicked(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            if self.gui.ui_state.current_menu_id != "interfaces":
                self.gui.show_menu("interfaces")

    def settings_cb(self, e):
        """Navigate to settings menu when settings button is clicked."""
        if e.get_code() == lv.EVENT.CLICKED:
            if self.gui.ui_state.current_menu_id != "manage_settings":
                self.gui.show_menu("manage_settings")

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

        # Lock icon (always visible, but changes based on state)
        if locked:
            self.lock_btn.update_icon(BTC_ICONS.LOCK)
            # Hide peripheral indicators when locked
            self.qr_img.set_src(None)
            self.usb_img.set_src(None)
            self.sd_img.set_src(None)
            self.smartcard_img.set_src(None)
        else:
            self.lock_btn.update_icon(BTC_ICONS.UNLOCK)
            # Show peripheral indicators when unlocked
            if state.hasQR():
                if state.QR_enabled():
                    BTC_ICONS.QR_CODE(GREEN_HEX).add_to_parent(self.qr_img)
                else:
                    BTC_ICONS.QR_CODE(GREY_HEX).add_to_parent(self.qr_img)
            else:
                self.qr_img.set_src(None)

            if state.hasUSB():
                if state.USB_enabled():
                    BTC_ICONS.USB(WHITE_HEX).add_to_parent(self.usb_img)
                else:
                    BTC_ICONS.USB(GREY_HEX).add_to_parent(self.usb_img)
            else:
                self.usb_img.set_src(None)

            if state.hasSD():
                if state.SD_enabled():
                    if state.SD_detected():
                        BTC_ICONS.SD_CARD(GREEN_HEX).add_to_parent(self.sd_img)
                    else:
                        BTC_ICONS.SD_CARD(WHITE_HEX).add_to_parent(self.sd_img)
                else:
                    BTC_ICONS.SD_CARD(GREY_HEX).add_to_parent(self.sd_img)
            else:
                self.sd_img.set_src(None)

            if state.hasSmartCard():
                if state.SmartCard_enabled():
                    if state.SmartCard_detected():
                        BTC_ICONS.SMARTCARD(GREEN_HEX).add_to_parent(self.smartcard_img)
                    else:
                        BTC_ICONS.SMARTCARD(WHITE_HEX).add_to_parent(self.smartcard_img)
                else:
                    BTC_ICONS.SMARTCARD(GREY_HEX).add_to_parent(self.smartcard_img)
            else:
                self.smartcard_img.set_src(None)
