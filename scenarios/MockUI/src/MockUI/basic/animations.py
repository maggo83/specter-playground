"""Low-level LVGL animation helpers.

Each function prepares an lv.anim_t and returns it. The caller is responsible
for calling anim.start() — this ensures the ref is stored before the animation
(and its completion callback) can fire.

The exec callback (lambda) is kept alive by the anim_t binding internally, so
only the anim_t itself needs to be stored.

Typical usage::

    def _on_done(anim): ...
    a = slide_y(obj, from_y=H, to_y=0, duration_ms=200, on_done=_on_done)
    self._refs = [a]  # store ref first
    a.start()         # then start
"""

import lvgl as lv


def _slide(obj, from_value, to_value, duration_ms, axis, on_done=None):
    """Prepare (but do NOT start) an x or y slide animation.

    Snaps obj to from_value immediately (avoids first-frame flicker).
    Returns anim — caller must store it, then call anim.start().
    on_done(anim) is called by LVGL when the animation completes.
    """
    if axis == "x":
        obj.set_x(from_value)
        cb = lambda anim, v: obj.set_x(v)
    elif axis == "y":
        obj.set_y(from_value)
        cb = lambda anim, v: obj.set_y(v)
    a = lv.anim_t()
    a.init()
    a.set_custom_exec_cb(cb)
    a.set_values(from_value, to_value)
    a.set_duration(duration_ms)
    if on_done is not None:
        a.set_completed_cb(on_done)
    return a

def slide_x(obj, from_x, to_x, duration_ms, on_done=None):
    """Prepare (but do NOT start) an x slide. Returns anim."""
    return _slide(obj, from_x, to_x, duration_ms, axis="x", on_done=on_done)

def slide_y(obj, from_y, to_y, duration_ms, on_done=None):
    """Prepare (but do NOT start) a y slide. Returns anim."""
    return _slide(obj, from_y, to_y, duration_ms, axis="y", on_done=on_done)