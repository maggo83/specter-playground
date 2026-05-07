"""Base class for all views (menus, action screens, etc.) that have a title.

Provides a fixed-height title bar at the top (containing a centred title 
label) and a body area below it that fills the emaining space.
Subclasses place their specific content inside self.body.

Layout (absolute, no flex on root):
    ┌────────────────────────────────────────┐
    │  title_bar  (TITLE_ROW_HEIGHT px)      │
    ├────────────────────────────────────────┤
    │  (TITLE_PADDING gap)                   │
    ├────────────────────────────────────────┤
    │  body  (fills remaining height)        │
    └────────────────────────────────────────┘
"""

import lvgl as lv
from .ui_consts import TITLE_ROW_HEIGHT, TITLE_PADDING, SCREEN_HEIGHT, CONTENT_PCT, TITLE_FONT
from .widgets.labels import body_label
from .specter_gui_base import SpecterGuiElement


class TitledScreen(SpecterGuiElement):
    """Base class for all views that have a title.

    Attributes available to subclasses:
        self.gui         - the SpecterGui that owns this screen
        self.device_state - gui.device_state shorthand
        self.ui_state    - gui.ui_state shorthand
        self.i18n        - gui.i18n shorthand
        self.on_navigate - navigation callback from gui.on_navigate
        self.title_bar   - lv.obj strip at the top, TITLE_ROW_HEIGHT tall
        self.title       - lv.label centred inside title_bar  (alias: self.title)
        self.body        - lv.obj below the title bar; put content here
    """

    def __init__(self, title, parent):
        #If parent in GUI itself, anchor titled screen just to the content area, 
        # so it doesn't cover the nav bar.
        lv_parent = getattr(parent, "content", parent)
        super().__init__(lv_parent)

        #convenience shortcuts
        self.gui = parent

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
        self.title = body_label(self.title_bar, title, font=TITLE_FONT)
        self.title.align(lv.ALIGN.CENTER, 0, 0)


        # ── Body ─────────────────────────────────────────────────────────────
        # Height = content area height minus the title bar and padding, so
        # the body matches the actual visible space.
        body_height = SCREEN_HEIGHT * CONTENT_PCT // 100 - TITLE_ROW_HEIGHT - TITLE_PADDING
        self.body = lv.obj(self)
        self.body.set_width(lv.pct(100))
        self.body.set_height(body_height)
        self.body.set_style_pad_all(0, 0)
        self.body.set_style_border_width(0, 0)
        self.body.set_style_radius(0, 0)
        self.body.align(lv.ALIGN.TOP_MID, 0, TITLE_ROW_HEIGHT + TITLE_PADDING)
        # Disable all scrolling on body; subclasses can re-enable with set_scroll_dir if needed
        self.body.set_scroll_dir(lv.DIR.NONE)

    def on_back(self, e):
        if e.get_code() == lv.EVENT.CLICKED:
            self.on_navigate(None)
