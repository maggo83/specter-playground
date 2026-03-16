
import lvgl as lv
import urandom
from ..basic import TitledScreen, BTN_HEIGHT, BTN_WIDTH
from ..basic.keyboard_manager import Layout
from ..stubs import Seed


class GenerateSeedMenu(TitledScreen):
    """Form to generate a new MasterKey (seedphrase).

    Creates a Seed object; the default wallet is auto-created by
    SpecterState.add_seed().

    menu_id: "generate_seedphrase"
    """

    def __init__(self, parent):
        super().__init__(parent.i18n.t("MENU_GENERATE_SEEDPHRASE"), parent)
        t = self.i18n.t

        self.body.set_layout(lv.LAYOUT.FLEX)
        self.body.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.body.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        # Key name row
        name_row = lv.obj(self.body)
        name_row.set_width(lv.pct(100))
        name_row.set_height(70)
        name_row.set_layout(lv.LAYOUT.FLEX)
        name_row.set_flex_flow(lv.FLEX_FLOW.ROW)
        name_row.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        name_row.set_style_border_width(0, 0)
        name_row.set_style_pad_all(0, 0)

        name_lbl = lv.label(name_row)
        name_lbl.set_text(t("GENERATE_SEED_KEY_NAME"))
        name_lbl.set_width(lv.pct(30))
        name_lbl.set_style_text_align(lv.TEXT_ALIGN.LEFT, 0)
        name_lbl.set_style_text_font(lv.font_montserrat_22, 0)

        # editable text area
        self.name_ta = lv.textarea(name_row)
        self.name_ta.set_text("Key " + str(urandom.randint(1, 99)))
        self._original_name = self.name_ta.get_text()
        self.name_ta.set_width(lv.pct(60))
        self.name_ta.set_height(50)
        self.name_ta.set_style_text_font(lv.font_montserrat_22, 0)

        keyboard_binder = lambda e: self.gui.keyboard_manager.bind(self.name_ta, Layout.FULL)
        self.name_ta.add_event_cb(keyboard_binder, lv.EVENT.CLICKED, None)

        # Fingerprint preview
        self.generated_fp = self._generate_dummy_fp()
        fp_lbl = lv.label(self.body)
        fp_lbl.set_text(t("GENERATE_SEED_FINGERPRINT") + self.generated_fp)
        fp_lbl.set_width(lv.pct(100))
        fp_lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        fp_lbl.set_style_text_font(lv.font_montserrat_16, 0)

        # Info text
        info_lbl = lv.label(self.body)
        info_lbl.set_text(t("GENERATE_SEED_INFO"))
        info_lbl.set_width(lv.pct(90))
        info_lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        info_lbl.set_style_text_font(lv.font_montserrat_16, 0)
        info_lbl.set_style_text_color(lv.color_hex(0x888888), 0)

        # Create button row
        create_row = lv.obj(self.body)
        create_row.set_width(lv.pct(100))
        create_row.set_height(80)
        create_row.set_layout(lv.LAYOUT.FLEX)
        create_row.set_flex_flow(lv.FLEX_FLOW.ROW)
        create_row.set_flex_align(lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        create_row.set_style_border_width(0, 0)
        create_row.set_style_pad_all(0, 0)

        self.create_btn = lv.button(create_row)
        self.create_btn.set_width(lv.pct(BTN_WIDTH))
        self.create_btn.set_height(BTN_HEIGHT)
        self.create_lbl = lv.label(self.create_btn)
        self.create_lbl.set_text(t("GENERATE_SEED_CREATE"))
        self.create_lbl.set_style_text_font(lv.font_montserrat_22, 0)
        self.create_lbl.center()
        self.create_btn.add_event_cb(lambda e: self._on_create(e), lv.EVENT.CLICKED, None)

    def _generate_dummy_fp(self):
        try:
            r = urandom.getrandbits(32)
            h = hex(r)[2:]
            return "0" * (8 - len(h)) + h
        except Exception:
            import utime
            h = hex(int(utime.ticks_ms()) & 0xFFFFFFFF)[2:]
            return "0" * (8 - len(h)) + h

    def _on_create(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return

        # read name
        name = self.name_ta.get_text()

        # create seed — add_seed() auto-creates default wallet
        seed = Seed(label=name, fingerprint=self.generated_fp)
        self.state.add_seed(seed)

        # go to main menu directly
        if hasattr(self.gui, 'ui_state') and self.gui.ui_state:
            self.gui.ui_state.clear_history()
            self.gui.ui_state.current_menu_id = "main"
        self.on_navigate(None)