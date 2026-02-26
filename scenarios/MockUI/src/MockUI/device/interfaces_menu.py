import lvgl as lv
from ..basic import SWITCH_HEIGHT, SWITCH_WIDTH
from ..basic.titled_screen import TitledScreen
from ..basic.symbol_lib import BTC_ICONS

class InterfacesMenu(TitledScreen):
    """Menu to enable/disable hardware interfaces.

    menu_id: "interfaces"
    """

    def __init__(self, parent, *args, **kwargs):
        # Get translation function early (needed for title)
        self.t = parent.i18n.t
        # TitledScreen creates title_bar (with optional back_btn + title_lbl) and body
        super().__init__(self.t("MENU_ENABLE_DISABLE_INTERFACES"), parent, *args, **kwargs)

        self.state = getattr(parent, "specter_state", None)
        self.parent = parent
        self.menu_id = "interfaces"

        # Container for rows inside body
        self.container = self.body
        self.container.set_layout(lv.LAYOUT.FLEX)
        self.container.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.container.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        # Build interface rows: list of tuples (icon, label_text, state_attr)
        rows = []
        if self.state.hasQR:
            rows.append((BTC_ICONS.QR_CODE, self.t("HARDWARE_QR_CODE"), "enabledQR"))
        if self.state.hasUSB:
            rows.append((BTC_ICONS.USB, self.t("HARDWARE_USB"), "enabledUSB"))
        if self.state.hasSD:
            rows.append((BTC_ICONS.SD_CARD, self.t("HARDWARE_SD_CARD"), "enabledSD"))
        if self.state.hasSmartCard:
            rows.append((BTC_ICONS.SMARTCARD, self.t("HARDWARE_SMARTCARD"), "enabledSmartCard"))

        for icon, text, state_attr in rows:
            row = lv.obj(self.container)
            row.set_style_border_width(0, 0)

            row.set_width(lv.pct(100))
            row.set_height(SWITCH_HEIGHT+2)
            row.set_layout(lv.LAYOUT.FLEX)
            row.set_flex_flow(lv.FLEX_FLOW.ROW)
            row.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
            row.set_style_pad_row(0, 0)
            row.set_style_pad_column(8, 0)  # Space between icon and text

            # Left icon
            icon_img = lv.image(row)
            icon.add_to_parent(icon_img)

            # Text label
            lbl = lv.label(row)
            lbl.set_text(text)
            lbl.set_style_text_align(lv.TEXT_ALIGN.LEFT, 0)
            lbl.set_style_text_font(lv.font_montserrat_22, 0)
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

                # update specter_state stored on this menu instance and in NavigationController
                setattr(self.state, attr, is_on)
                setattr(self.parent.specter_state, attr, is_on)

                # refresh UI
                self.parent.refresh_ui()


            sw.add_event_cb(lambda e, a=state_attr: _handler(e, a), lv.EVENT.VALUE_CHANGED, None)



    def on_back(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            self.on_navigate(None)
