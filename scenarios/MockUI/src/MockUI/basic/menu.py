import lvgl as lv
from .ui_consts import BTN_HEIGHT, BTN_WIDTH, MODAL_HEIGHT_PCT, MODAL_WIDTH_PCT, PAD_SIZE
from .titled_screen import TitledScreen
from .symbol_lib import Icon, BTC_ICONS
from .modal_overlay import ModalOverlay


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

    def _build_menu_items(self, menu_items):
        """Build LVGL widgets for each item in the menu_items list."""
        for item in menu_items:
            # Extract tuple elements: (icon, text, target_behavior, color, size, help_key)
            icon, text, target_behavior, color, size, help_key = item

            # Normalize size: default to 1, ensure minimum of 1
            if size is None or size < 1:
                size = 1

            if target_behavior is None:
                spacer = lv.label(self.body)
                spacer.set_recolor(True)
                spacer.set_text(text or "")
                spacer.set_width(lv.pct(BTN_WIDTH))
                spacer.set_style_text_align(lv.TEXT_ALIGN.LEFT, 0)
                spacer.set_style_text_font(lv.font_montserrat_22, 0)
            else:
                btn = lv.button(self.body)
                btn.set_width(lv.pct(BTN_WIDTH))
                # Apply size scaling to button height
                scaled_height = int(BTN_HEIGHT * size)
                btn.set_height(scaled_height)
                if color:
                    btn.set_style_bg_color(color, lv.PART.MAIN)

                if icon:
                    # Check if icon is an Icon
                    if isinstance(icon, Icon):
                        icon_img = lv.image(btn)
                        icon.add_to_parent(icon_img)
                        icon_img.align(lv.ALIGN.LEFT_MID, 8, 0)
                    else:
                        # Traditional string icon (lv.SYMBOL.*)
                        ico = lv.label(btn)
                        ico.set_recolor(True)
                        ico.set_text(icon or "")
                        ico.align(lv.ALIGN.LEFT_MID, 8, 0)

                # Add text label centered
                lbl = lv.label(btn)
                lbl.set_recolor(True)
                lbl.set_text(text)
                lbl.set_style_text_font(lv.font_montserrat_22, 0)
                lbl.center()

                # Add help icon on right side if help_key is provided
                if help_key:
                    help_btn = lv.button(btn)
                    help_btn.set_size(int(BTN_HEIGHT), int(BTN_HEIGHT * size))
                    # Make the help button transparent (no background)
                    help_btn.set_style_bg_opa(lv.OPA.TRANSP, 0)
                    help_btn.set_style_shadow_width(0, 0)
                    help_btn.set_style_border_width(0, 0)
                    help_btn.align(lv.ALIGN.RIGHT_MID, -4, 0)

                    help_icon_img = lv.image(help_btn)
                    BTC_ICONS.QUESTION_CIRCLE.add_to_parent(help_icon_img)
                    help_icon_img.center()

                    # Create help popup callback
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

                dialog = lv.obj(modal.overlay)
                dialog.set_size(dw, dh)
                dialog.set_pos(dx, dy)
                dialog.set_style_radius(8, 0)
                dialog.set_style_border_width(0, 0)
                dialog.set_style_pad_all(12, 0)
                dialog.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
                dialog.set_layout(lv.LAYOUT.FLEX)
                dialog.set_flex_flow(lv.FLEX_FLOW.COLUMN)
                dialog.set_flex_align(lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

                # title
                title_lbl = lv.label(dialog)
                title_lbl.set_text(title_text)
                title_lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
                title_lbl.set_style_text_font(lv.font_montserrat_22, 0)
                title_lbl.set_width(lv.pct(100))

                # body text
                text_lbl = lv.label(dialog)
                text_lbl.set_text(help_text)
                text_lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
                text_lbl.set_style_text_font(lv.font_montserrat_22, 0)
                text_lbl.set_width(lv.pct(100))
                text_lbl.set_long_mode(lv.label.LONG_MODE.WRAP)

                # close button
                close_btn = lv.button(dialog)
                close_lbl = lv.label(close_btn)
                close_lbl.set_text(self.i18n.t("MODAL_CLOSE_BTN"))
                close_lbl.set_style_text_font(lv.font_montserrat_22, 0)
                close_lbl.center()

                def _close(ev):
                    if ev.get_code() == lv.EVENT.CLICKED:
                        modal.close()

                close_btn.add_event_cb(_close, lv.EVENT.CLICKED, None)

                # stop the underlying button from firing too
                e.stop_bubbling = 1
        return callback

    def on_back(self, e):
        self.on_navigate(None)
