"""Base class for all full-screen views (menus, action screens, etc.).

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
from .ui_consts import BACK_BTN_HEIGHT, BACK_BTN_WIDTH, TITLE_ROW_HEIGHT, TITLE_PADDING
from .symbol_lib import BTC_ICONS


class TitledScreen(lv.obj):
    """Base class for all full-screen views.

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

        # Back button – only shown when there is navigation history
        if parent.ui_state and parent.ui_state.history and len(parent.ui_state.history) > 0:
            self.back_btn = lv.button(self.title_bar)
            self.back_btn.set_size(BACK_BTN_HEIGHT, BACK_BTN_WIDTH)
            self.back_btn.align(lv.ALIGN.LEFT_MID, 8, 0)
            self.back_ico = lv.image(self.back_btn)
            BTC_ICONS.CARET_LEFT.add_to_parent(self.back_ico)
            self.back_ico.center()
            self.back_btn.add_event_cb(lambda e: self.on_back(e), lv.EVENT.CLICKED, None)

        # Title label – centred in the title bar
        self.title_lbl = lv.label(self.title_bar)
        self.title_lbl.set_text(title)
        self.title_lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.title_lbl.set_style_text_font(lv.font_montserrat_28, 0)
        self.title_lbl.align(lv.ALIGN.CENTER, 0, 0)
        # Backward-compat alias (WalletMenu and tests reference self.title)
        self.title = self.title_lbl

        # ── Body ─────────────────────────────────────────────────────────────
        # Sits below the title bar.  Height = 100% of root so LVGL clips
        # anything that falls below the parent edge – no pixel arithmetic needed.
        self.body = lv.obj(self)
        self.body.set_width(lv.pct(100))
        self.body.set_height(lv.pct(100))
        self.body.set_style_pad_all(0, 0)
        self.body.set_style_border_width(0, 0)
        self.body.set_style_radius(0, 0)
        self.body.align(lv.ALIGN.TOP_MID, 0, TITLE_ROW_HEIGHT + TITLE_PADDING)
        # Disable all scrolling on body; subclasses can re-enable with set_scroll_dir if needed
        self.body.set_scroll_dir(lv.DIR.NONE)

    def on_back(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            self.on_navigate(None)
