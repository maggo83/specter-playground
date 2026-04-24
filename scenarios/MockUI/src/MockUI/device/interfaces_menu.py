import lvgl as lv
from ..basic import SWITCH_HEIGHT, SWITCH_WIDTH
from ..basic.titled_screen import TitledScreen
from ..basic.symbol_lib import BTC_ICONS
from ..basic.widgets import flex_row, form_label

class InterfacesMenu(TitledScreen):
    """Menu to enable/disable hardware interfaces."""

    def __init__(self, parent):
        # TitledScreen sets self.gui, self.state, self.i18n, self.on_navigate
        super().__init__(parent.i18n.t("MENU_ENABLE_DISABLE_INTERFACES"), parent)

        # Container for rows inside body
        self.body.set_layout(lv.LAYOUT.FLEX)
        self.body.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.body.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        # Build interface rows: list of tuples (icon, label_text, state_attr)
        rows = []
        if self.state.hasQR():
            rows.append((BTC_ICONS.QR_CODE, self.i18n.t("HARDWARE_QR_CODE"), "_enabledQR"))
        if self.state.hasUSB():
            rows.append((BTC_ICONS.USB, self.i18n.t("HARDWARE_USB"), "_enabledUSB"))
        if self.state.hasSD():
            rows.append((BTC_ICONS.SD_CARD, self.i18n.t("HARDWARE_SD_CARD"), "_enabledSD"))
        if self.state.hasSmartCard():
            rows.append((BTC_ICONS.SMARTCARD, self.i18n.t("HARDWARE_SMARTCARD"), "_enabledSmartCard"))

        for icon, text, state_attr in rows:
            row = flex_row(self.body, height=SWITCH_HEIGHT + 2, main_align=lv.FLEX_ALIGN.START)
            row.set_style_pad_column(8, 0)  # Space between icon and text

            # Left icon
            icon_img = lv.image(row)
            icon.add_to_parent(icon_img)

            # Text label
            lbl = form_label(row, text, width=None)
            lbl.set_flex_grow(1)  # Take remaining space

            # Right toggle button
            sw = lv.switch(row)
            sw.set_size(SWITCH_HEIGHT, SWITCH_WIDTH)

            # Set initial state from specter_state (if present)
            enabled = bool(getattr(self.state, state_attr))
            if enabled:
                #sw.on(lv.ANIM.OFF)
                sw.add_state(lv.STATE.CHECKED)
            else:
                sw.remove_state(lv.STATE.CHECKED)

            # Event handler: single handler function and a lambda that binds
            # the current state_attr into its default argument so each switch
            # receives the correct attribute (avoids late-binding loop issue).
            def _handler(e, attr):
                sw_obj = e.get_target_obj()
                is_on = bool(sw_obj.has_state(lv.STATE.CHECKED))

                # update specter_state via shorthand
                setattr(self.state, attr, is_on)

                # refresh UI
                self.gui.refresh_ui()


            sw.add_event_cb(lambda e, a=state_attr: _handler(e, a), lv.EVENT.VALUE_CHANGED, None)
