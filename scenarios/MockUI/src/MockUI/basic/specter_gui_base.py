"""specter_gui_base — GUI context access helpers.

Two classes are provided so each consumer picks the right base:

``SpecterGuiMixin``
    Pure-Python base.  Provides ``state``/``i18n``/``t``/``on_navigate`` as
    properties resolved from ``self.gui``.  Use for controllers that are not
    LVGL widgets.

``SpecterGuiElement``
    ``lv.obj`` subclass with the same four properties.  Use for concrete LVGL
    widgets (``TitledScreen``, ``NavigationBar``, …).

MicroPython does not support multiple inheritance, so both classes define the
same four properties independently.
"""
import lvgl as lv


class SpecterGuiMixin:
    """Pure-Python base: ``state``, ``i18n``, ``t``, ``on_navigate`` from ``self.gui``."""

    @property
    def state(self):
        return self.gui.specter_state

    @property
    def i18n(self):
        return self.gui.i18n

    @property
    def t(self):
        return self.gui.i18n.t

    @property
    def on_navigate(self):
        return self.gui.on_navigate


class SpecterGuiElement(lv.obj):
    """``lv.obj`` subclass: ``state``, ``i18n``, ``t``, ``on_navigate`` from ``self.gui``."""

    @property
    def state(self):
        return self.gui.specter_state

    @property
    def i18n(self):
        return self.gui.i18n

    @property
    def t(self):
        return self.gui.i18n.t

    @property
    def on_navigate(self):
        return self.gui.on_navigate
