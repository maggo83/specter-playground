
import lvgl as lv
from ..basic import GREY_HEX, TitledScreen, BTN_HEIGHT, BTN_WIDTH
from ..basic.keyboard_manager import Layout
from ..basic.widgets import flex_row, form_label, form_textarea, Btn, body_label
from ..stubs import Seed
import urandom


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
        name_row = flex_row(self.body, height=70, main_align=lv.FLEX_ALIGN.START)

        form_label(name_row, t("COMMON_NAME"))

        # editable text area
        self.name_ta = form_textarea(name_row)
        self.name_ta.set_text("Key " + str(urandom.randint(1, 99)))

        keyboard_binder = lambda e: self.gui.keyboard_manager.bind(self.name_ta, Layout.FULL)
        self.name_ta.add_event_cb(keyboard_binder, lv.EVENT.CLICKED, None)

        # Fingerprint preview
        self.generated_fp = Seed.generate_dummy_fingerprint()
        body_label(self.body,
                   t("GENERATE_SEED_FINGERPRINT") + self.generated_fp,
                   font=lv.font_montserrat_16)

        # Info text
        body_label(self.body, t("GENERATE_SEED_INFO"),
                   font=lv.font_montserrat_16,
                   width=lv.pct(90),
                   color=GREY_HEX)

        # Create button row
        create_row = flex_row(self.body, height=80)

        self.create_btn = Btn(
            create_row,
            text=t("COMMON_CREATE"),
            size=(lv.pct(BTN_WIDTH), BTN_HEIGHT),
            callback=lambda e: self._on_create(e),
        )

    def _on_create(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return

        # read name before any navigation (the textarea is destroyed on refresh)
        name = self.name_ta.get_text()

        # create seed — add_seed() auto-creates default wallet
        seed = Seed(label=name, fingerprint=self.generated_fp)
        self.state.add_seed(seed)

        # Navigate to main. Set current_menu_id first, then call refresh_ui()
        # directly — do NOT call on_navigate(None) because that calls pop_menu()
        # which would restore the history entry for this screen, rebuilding it
        # with a fresh random name instead of navigating away.
        if hasattr(self.gui, 'ui_state') and self.gui.ui_state:
            self.gui.ui_state.clear_history()
            self.gui.ui_state.current_menu_id = "main"
        self.gui.refresh_ui()