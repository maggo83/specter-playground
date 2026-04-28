"""Base class for all views (menus, action screens, etc.) that have a title.

Provides a fixed-height title bar at the top (containing an optional back
button and a centred title label) and a body area below it that fills the
remaining space.  Subclasses place their specific content inside self.body.

Layout (absolute, no flex on root):
    ┌────────────────────────────────────────┐
    │  title_bar  (TITLE_ROW_HEIGHT px)      │
    │  [back_btn]    [title_lbl (centred)]   │
    ├────────────────────────────────────────┤
    │  (TITLE_PADDING gap)                   │
    ├────────────────────────────────────────┤
    │  body  (fills remaining height)        │
    └────────────────────────────────────────┘
"""

import lvgl as lv
from .ui_consts import BACK_BTN_HEIGHT, BACK_BTN_WIDTH, TITLE_ROW_HEIGHT, TITLE_PADDING, SCREEN_HEIGHT, CONTENT_PCT
from .widgets.labels import body_label


class TitledScreen(lv.obj):
    """Base class for all views that have a title.

    Attributes available to subclasses:
        self.gui        – the SpecterGui that owns this screen
        self.state      – gui.specter_state shorthand
        self.i18n       – gui.i18n shorthand
        self.on_navigate – navigation callback from gui.on_navigate
        self.title_bar  – lv.obj strip at the top, TITLE_ROW_HEIGHT tall
        self.title_lbl  – lv.label centred inside title_bar  (alias: self.title)
        self.back_btn   – lv.button in title_bar (only when navigation history exists)
        self.body       – lv.obj below the title bar; put content here
    """

    def __init__(self, title, parent):
        lv_parent = getattr(parent, "content", parent)
        super().__init__(lv_parent)

        self.gui = parent
        self.state = getattr(parent, "specter_state", None)
        self.i18n = getattr(parent, "i18n", None)
        self.on_navigate = getattr(parent, "on_navigate", None)

        # Root: fill parent completely, no decoration
        self.set_width(lv.pct(100))
        self.set_height(lv.pct(100))
        self.set_style_pad_all(0, 0)
        self.set_style_border_width(0, 0)
        self.set_style_radius(0, 0)
        self.set_scroll_dir(lv.DIR.NONE)

        # ── Title bar ────────────────────────────────────────────────────────
        self.title_bar = lv.obj(self)
        self.title_bar.set_width(lv.pct(100))
        self.title_bar.set_height(TITLE_ROW_HEIGHT)
        self.title_bar.set_style_pad_all(0, 0)
        self.title_bar.set_style_border_width(0, 0)
        self.title_bar.set_style_radius(0, 0)
        self.title_bar.align(lv.ALIGN.TOP_MID, 0, 0)

        # Title label – centred in the title bar
        self.title_lbl = body_label(self.title_bar, title, font=lv.font_montserrat_28)
        self.title_lbl.align(lv.ALIGN.CENTER, 0, 0)
        # Backward-compat alias (WalletMenu and tests reference self.title)
        self.title = self.title_lbl

        # ── Body ─────────────────────────────────────────────────────────────
        # Height = content area height minus the title bar and padding, so
        # the body matches the actual visible space. This lets LVGL's scroll
        # detection work correctly: content taller than this value scrolls.
        _body_height = SCREEN_HEIGHT * CONTENT_PCT // 100 - TITLE_ROW_HEIGHT - TITLE_PADDING
        self.body = lv.obj(self)
        self.body.set_width(lv.pct(100))
        self.body.set_height(_body_height)
        self.body.set_style_pad_all(0, 0)
        self.body.set_style_border_width(0, 0)
        self.body.set_style_radius(0, 0)
        self.body.align(lv.ALIGN.TOP_MID, 0, TITLE_ROW_HEIGHT + TITLE_PADDING)
        # Disable all scrolling on body; subclasses can re-enable with set_scroll_dir if needed
        self.body.set_scroll_dir(lv.DIR.NONE)

    def on_back(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            self.on_navigate(None)
