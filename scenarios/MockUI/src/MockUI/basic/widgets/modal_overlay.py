"""ModalOverlay — shared base for all full-screen layer_top overlays.

Any UI element that needs to sit above everything else (help modals, guided
tour explainers, confirmation dialogs, …) should create a ModalOverlay and
attach its content to ``self.overlay``.

Why layer_top?
    LVGL composites layer_top above every screen child regardless of z-order,
    so this is the only reliable way to display a modal that:
      - covers the entire display
      - captures all touch input
      - is not clipped by any parent container

Usage::

    modal = ModalOverlay(bg_opa=180)           # semi-transparent dark backdrop
    modal = ModalOverlay(bg_opa=lv.OPA.TRANSP) # transparent (add dim strips yourself)

    # build your content as children of modal.overlay
    dialog = lv.obj(modal.overlay)
    ...

    # dismiss
    modal.close()
"""

import lvgl as lv
from ..ui_consts import DEFAULT_MODAL_BG_OPA, BLACK, to_lv_color

class ModalOverlay:
    """Full-screen container parented to ``layer_top``.

    Args:
        bg_opa:   Background opacity (0-255 or ``lv.OPA.*`` constant).
                  Use ``lv.OPA.TRANSP`` when adding your own dim strips.
        bg_color: Background colour as a hex int (default: BLACK_HEX).
    """

    def __init__(self, bg_opa=DEFAULT_MODAL_BG_OPA, bg_color=BLACK):
        disp = lv.display_get_default()
        self._sw = disp.get_horizontal_resolution()
        self._sh = disp.get_vertical_resolution()

        self.overlay = lv.obj(disp.get_layer_top())
        self.overlay.set_size(self._sw, self._sh)
        self.overlay.set_pos(0, 0)
        self.overlay.set_style_bg_color(to_lv_color(bg_color), 0)
        self.overlay.set_style_bg_opa(bg_opa, 0)
        self.overlay.set_style_border_width(0, 0)
        self.overlay.set_style_radius(0, 0)
        self.overlay.set_style_pad_all(0, 0)
        self.overlay.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

    @property
    def screen_width(self):
        return self._sw

    @property
    def screen_height(self):
        return self._sh

    def close(self):
        """Delete the overlay and all its children."""
        if self.overlay is not None:
            self.overlay.delete()
            self.overlay = None
