"""Btn — unified button widget for the Specter MockUI.

A single class that handles all button variants:
  - icon-only:        Btn(parent, icon=BTC_ICONS.CARET_LEFT, size=(60, 50), callback=cb)
  - text-only:        Btn(parent, text="Cancel", size=(lv.pct(100), BTN_HEIGHT), callback=cb)
  - icon + text:      Btn(parent, icon=BTC_ICONS.TRASH, text="Delete", color=RED_HEX, callback=cb)
  - transparent/ghost: Btn(parent, size=(60, 50), callback=cb).make_transparent()
  - placeholder:      Btn(parent, size=(60, 50)).placeholder()

Size parameter is a (width, height) tuple; either element may be None to skip setting it.

Proxy: all lv.button methods are accessible directly on Btn instances (e.g. btn.align(...)).
"""

import lvgl as lv
from ..symbol_lib import Icon


class Btn:
    """Unified LVGL button wrapper with Specter default styling.

    Args:
        parent:   LVGL parent object.
        icon:     Icon instance (e.g. BTC_ICONS.TRASH), or None.
        text:     Label string, or None.
        color:    lv.color background override, or None (theme default).
        size:     (width, height) tuple; either element may be None = don't set.
        callback: Zero-argument callable, or an lv.EVENT handler with signature
                  ``fn(event)``.  Attached to lv.EVENT.CLICKED.
        font:     LVGL font for the text label; defaults to lv.font_montserrat_22.
    """

    def __init__(self, parent, icon=None, text=None, color=None, size=None,
                 callback=None, font=None):
        self._btn = lv.button(parent)

        if size is not None:
            w, h = size
            if w is not None:
                self._btn.set_width(w)
            if h is not None:
                self._btn.set_height(h)

        if color is not None:
            self._btn.set_style_bg_color(color, lv.PART.MAIN)

        # If both icon and text: flex row so they sit side by side
        if icon is not None and text is not None:
            self._btn.set_layout(lv.LAYOUT.FLEX)
            self._btn.set_flex_flow(lv.FLEX_FLOW.ROW)
            self._btn.set_flex_align(
                lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER
            )

        if icon is not None:
            self._ico_img = lv.image(self._btn)
            icon.add_to_parent(self._ico_img)
            if text is None:
                self._ico_img.center()
        else:
            self._ico_img = None

        if text is not None:
            lbl = lv.label(self._btn)
            lbl.set_text(text)
            lbl.set_style_text_font(
                font if font is not None else lv.font_montserrat_22, 0
            )
            if icon is None:
                lbl.center()

        if callback is not None:
            self._btn.add_event_cb(callback, lv.EVENT.CLICKED, None)

    def update_icon(self, icon, color=None):
        """Replace the displayed icon (must have been created with an icon).

        Args:
            icon:  BTC_ICONS entry to display.
            color: Optional lv.color to recolour the icon; None keeps default.
        """
        if self._ico_img is not None:
            if color is not None:
                icon(color).add_to_parent(self._ico_img)
            else:
                icon.add_to_parent(self._ico_img)

    def make_transparent(self):
        """Remove button background, border and shadow.

        The button remains clickable and any icon/text content stays visible;
        only the button body itself becomes invisible.
        """
        self._btn.set_style_bg_opa(lv.OPA.TRANSP, 0)
        self._btn.set_style_shadow_width(0, 0)
        self._btn.set_style_border_width(0, 0)
        self._btn.set_style_radius(0, 0)
        self._btn.set_style_pad_all(0, 0)
        self._btn.set_style_margin_all(0, 0)
        return self

    def placeholder(self):
        """Invisible, non-clickable spacer (transparent body, no touch events).

        Use to occupy space in a flex row when no real button is needed,
        so sibling buttons stay correctly aligned.
        """
        self.make_transparent()
        self._btn.remove_flag(lv.obj.FLAG.CLICKABLE)
        return self

    def __getattr__(self, name):
        # Proxy all unknown attributes to the underlying lv.button.
        # Guard against recursion before _btn is initialised.
        if name == '_btn':
            raise AttributeError('_btn')
        return getattr(self._btn, name)
