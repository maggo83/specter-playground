import lvgl as lv
from .ui_consts import BTN_HEIGHT, BTN_WIDTH
from .titled_screen import TitledScreen

class ActionScreen(TitledScreen):
    """Generic action screen for menu items."""
    def __init__(self, title, parent):
        # TitledScreen creates title_bar (with optional back_btn + title_lbl) and body
        super().__init__(title, parent)

        # Get i18n manager from parent (always available via NavigationController)
        self.t = parent.i18n.t

        # Message – placed inside body
        self.msg = lv.label(self.body)
        self.msg.set_text(self.t("ACTION_SCREEN_PREFIX") + title)
        self.msg.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.msg.align(lv.ALIGN.TOP_MID, 0, 20)

        # Back button – placed inside body below the message
        self.action_back_btn = lv.button(self.body)
        self.action_back_btn.set_width(lv.pct(BTN_WIDTH))
        self.action_back_btn.set_height(BTN_HEIGHT)
        back_lbl = lv.label(self.action_back_btn)
        back_lbl.set_text(self.t("ACTION_SCREEN_BACK"))
        back_lbl.set_style_text_font(lv.font_montserrat_22, 0)
        back_lbl.center()
        self.action_back_btn.align_to(self.msg, lv.ALIGN.OUT_BOTTOM_MID, 0, 40)
        self.action_back_btn.add_event_cb(self.on_back, lv.EVENT.CLICKED, None)
