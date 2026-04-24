import lvgl as lv
from .ui_consts import BTN_HEIGHT, BTN_WIDTH, MODAL_HEIGHT_PCT, MODAL_WIDTH_PCT, PAD_SIZE
from .titled_screen import TitledScreen
from .symbol_lib import Icon, BTC_ICONS
from .widgets.modal_overlay import ModalOverlay
from .widgets.btn import Btn
from .widgets.containers import flex_col, dialog_card
from .widgets.labels import body_label, section_header



class GenericMenu(TitledScreen):
    """Reusable menu builder — template method pattern.

    Subclasses override the three hooks:
        get_title(t, state)      -> str          title shown at the top
        get_menu_items(t, state) -> list         list of (icon, text, target_behavior, color, size, help_key); will be used to create the actual menu
        post_init(t, state)      -> None         called after all LVGL widgets are built

    Each tuple element of menu_items:
        - icon: Icon object or lv.SYMBOL string
        - text: Display text for the menu item
        - target_behavior: None (creates label/spacer), string (menu_id to navigate to), or callable
        - color: (Optional) color for the button
        - size: (Optional) size multiplier for button height (default=1, minimum=1)
        - help_key: (Optional) i18n key for a help popup
    """

    def __init__(self, parent):
        # TitledScreen sets self.gui, self.state, self.i18n, self.on_navigate, self.body, etc.
        super().__init__("", parent)

        title = self.get_title(self.i18n.t, self.state)
        self.title_lbl.set_text(title)

        menu_items = self.get_menu_items(self.i18n.t, self.state)

        self.body.set_layout(lv.LAYOUT.FLEX)
        self.body.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.body.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        self._build_menu_items(menu_items)
        self.post_init(self.i18n.t, self.state)
        self._configure_scroll()

    def _configure_scroll(self):
        """Enable vertical scrolling only when content overflows the visible body.

        Forces a layout pass first so child positions are accurate, then scans
        all children to find the actual content extent. This way post_init
        additions are automatically included and no manual height tracking is
        needed. Also zeroes pad_bottom to prevent the theme’s default 13 px
        bottom padding from creating a phantom over-drag zone.
        """
        self.body.update_layout()
        content_h = 0
        for i in range(self.body.get_child_count()):
            child = self.body.get_child(i)
            bottom = child.get_y() + child.get_height()
            if bottom > content_h:
                content_h = bottom
        available_h = (self.body.get_height()
                       - self.body.get_style_pad_top(0)
                       - self.body.get_style_pad_bottom(0))
        if content_h > available_h:
            self.body.set_scroll_dir(lv.DIR.VER)
            self.body.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)
            self.body.remove_flag(lv.obj.FLAG.SCROLL_ELASTIC)
            self.body.remove_flag(lv.obj.FLAG.SCROLL_MOMENTUM)
            # Zero pad_bottom so LVGL's scroll_bottom formula
            # (last_child_bottom + pad_bottom - body_bottom) gives the exact
            # overflow. Then force a second layout pass so LVGL recalculates
            # scroll_bottom with the updated padding value.
            self.body.set_style_pad_bottom(0, 0)
            self.body.update_layout()
        else:
            self.body.set_scroll_dir(lv.DIR.NONE)
            self.body.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

    def _build_menu_items(self, menu_items):
        """Build LVGL widgets for each item in the menu_items list."""
        for item in menu_items:
            icon = item.icon
            text = item.text
            target_behavior = item.target
            color = item.color
            size = item.size
            help_key = item.help_key

            # Normalize size: default to 1, ensure minimum of 1
            if size is None or size < 1:
                size = 1

            if target_behavior is None:
                section_header(self.body, text, recolor=(text is not None and "#" in text))
            else:
                # Text-only Btn: icon is positioned manually at LEFT_MID so it
                # stays left-aligned regardless of text length (not using flex).
                btn = Btn(
                    self.body,
                    text=text,
                    color=color if color else None,
                    size=(lv.pct(BTN_WIDTH), int(BTN_HEIGHT * size)),
                )
                # Icon instance (BTC_ICONS.*) — add as image at left edge
                if icon and isinstance(icon, Icon):
                    ico_img = lv.image(btn._btn)
                    icon.add_to_parent(ico_img)
                    ico_img.align(lv.ALIGN.LEFT_MID, 8, 0)
                # String symbols (lv.SYMBOL.*) — add as recolor label at left edge
                elif icon and not isinstance(icon, Icon):
                    ico = body_label(btn._btn, icon or "", recolor=True, width=lv.SIZE_CONTENT)
                    ico.align(lv.ALIGN.LEFT_MID, 8, 0)

                # Add help icon on right side if help_key is provided
                if help_key:
                    help_btn = Btn(
                        btn._btn,
                        icon=BTC_ICONS.QUESTION_CIRCLE,
                        size=(int(BTN_HEIGHT), int(BTN_HEIGHT * size)),
                    )
                    help_btn.make_transparent()
                    help_btn.align(lv.ALIGN.RIGHT_MID, -4, 0)
                    help_btn.add_event_cb(self.make_help_callback(text, help_key), lv.EVENT.CLICKED, None)

                btn.add_event_cb(self.make_callback(target_behavior), lv.EVENT.CLICKED, None)

    # --- template-method hooks -------------------------------------------

    TITLE_KEY = None  # set in subclass to avoid overriding get_title

    def get_title(self, t, state):
        """Return the menu title string. Override in subclasses, or just set TITLE_KEY."""
        return t(self.TITLE_KEY) if self.TITLE_KEY else ""

    def get_menu_items(self, t, state):
        """Return the list of (icon, text, target_behavior, color, size, help_key) tuples."""
        return []

    def post_init(self, t, state):
        """Called after all LVGL widgets are built. Override for post-construction work."""
        pass

    # --- internal helpers -------------------------------------------------

    def make_callback(self, target_behavior):
        """Create callback for button - handles both string menu_ids and custom callables."""
        # If it's already a callable, return it directly
        if callable(target_behavior):
            return target_behavior
        
        # Otherwise, it's a string menu_id - create navigation callback
        def callback(e):
            if e.get_code() == lv.EVENT.CLICKED:
                if not self.on_navigate:
                    return
                if target_behavior == "back":
                    self.on_navigate(None)
                else:
                    self.on_navigate(target_behavior)
        return callback

    def make_help_callback(self, title_text, help_key):
        """Create callback for help button - shows a modal overlay with help text."""
        def callback(e):
            if e.get_code() == lv.EVENT.CLICKED:
                help_text = self.i18n.t(help_key)

                modal = ModalOverlay(bg_opa=180)
                sw = modal.screen_width
                sh = modal.screen_height

                # --- dialog card ---
                dw = sw * MODAL_WIDTH_PCT // 100
                dh = sh * MODAL_HEIGHT_PCT // 100
                dx = (sw - dw) // 2
                dy = (sh - dh) // 2

                dialog = dialog_card(modal.overlay, dw, dh, dx, dy)

                body_label(dialog, title_text)
                body_label(dialog, help_text)

                close_btn = Btn(
                    dialog,
                    text=self.i18n.t("MODAL_CLOSE_BTN"),
                    callback=lambda ev: modal.close() if ev.get_code() == lv.EVENT.CLICKED else None,
                )

                # stop the underlying button from firing too
                e.stop_bubbling = 1
        return callback

    def on_back(self, e):
        self.on_navigate(None)
