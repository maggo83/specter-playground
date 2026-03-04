"""On-device integration tests for the guided tour.

Test order matters: each test leaves the device in a known state for the next.
The module-scoped ``_fresh_tour_state`` fixture resets tour_completed=False
before any test in this file runs, so the auto-start sequence is reproducible
regardless of prior runs.

Index paths within layer_top (confirmed via live tree dump):
  layer_top → [0] overlay_obj → [1] content_obj
    [0] text_box   (label with step description)
    [1] nav_container
      [0] prev_btn     (_IDX_PREV)
      [1] skip_btn / checkmark_btn   (_IDX_SKIP_CHECK)
      [2] next_btn     (_IDX_NEXT)
"""
import ast
import json
import os
import time

import pytest

from conftest import (
    _load_label,
    _read_flash_json,
    disco_run,
    ensure_main_menu,
    find_labels_overlay,
    click_by_label,
    click_overlay_by_label,
    navigate_to_device_menu,
    soft_reset,
)

# Extract INTRO_TOUR_STEPS from source without executing any MicroPython code.
_NAV_SRC = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "src", "MockUI", "basic", "navigation_controller.py"
))

def _extract_intro_tour_steps(path: str) -> list:
    """Parse INTRO_TOUR_STEPS from navigation_controller.py using ast (no imports)."""
    tree = ast.parse(open(path).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "INTRO_TOUR_STEPS":
                    return ast.literal_eval(node.value)
    raise RuntimeError("INTRO_TOUR_STEPS not found in navigation_controller.py")

# Step keys extracted from static definition — no MicroPython needed.
STEP_KEYS = [step[1] for step in _extract_intro_tour_steps(_NAV_SRC)]

def _tour_overlay_content_idx() -> int:
    """Return the child index of the content box within the tour overlay wrapper.

    The ModalOverlay prepends dim strips so the content box is always the LAST
    child of layer_top.child(0).  Asserts an overlay is present.
    """
    out = disco_run(
        "repl", "exec",
        "import lvgl as lv; lt=lv.display_get_default().get_layer_top(); "
        "w=lt.get_child(0) if lt.get_child_count()>0 else None; "
        "print('NONE' if w is None else w.get_child_count())",
    )
    val = out.strip().splitlines()[-1] if out.strip() else ""
    assert val not in ("NONE", ""), "_tour_overlay_content_idx: no overlay present"
    return int(val) - 1


def _click_tour_nav(button: str, delay: float = 1.0) -> None:
    """Click a tour navigation button: 'prev', 'skip', or 'next'."""
    btn_idx = {"prev": 0, "skip": 1, "next": 2}.get(button)
    if btn_idx is None:
        raise ValueError(f"button must be 'prev', 'skip', or 'next', got {button!r}")

    last_idx = _tour_overlay_content_idx()

    out2 = disco_run(
        "repl", "exec",
        f"import lvgl as lv; lt=lv.display_get_default().get_layer_top(); "
        f"w=lt.get_child(0); c=w.get_child({last_idx}); nav=c.get_child(1); "
        f"btn=nav.get_child({btn_idx}); btn.send_event(lv.EVENT.CLICKED,None); print('OK')",
    )
    result = out2.strip().splitlines()[-1] if out2.strip() else ""
    assert result == "OK", f"_click_tour_nav({button!r}) failed: {out2!r}"
    time.sleep(delay)


# =========================================================================
# Helpers
# =========================================================================

def _tour_completed() -> bool:
    data = _read_flash_json("/flash/ui_state_config.json")
    return data.get("tour_completed", False)


def _reset_tour_state():
    """Write tour_completed=False to flash and soft-reset so tour auto-starts."""
    disco_run(
        "repl", "exec",
        "import json; f=open('/flash/ui_state_config.json','w'); "
        "json.dump({'tour_completed':False},f); f.close(); print('OK')",
    )
    soft_reset()
    ensure_main_menu()


# =========================================================================
# Module fixture: ensure a clean (tour not yet completed) state.
# =========================================================================

@pytest.fixture(scope="module", autouse=True)
def _fresh_tour_state():
    """Reset tour_completed=False and reboot before this test module runs."""
    _reset_tour_state()
    yield


# =========================================================================
# Tests — ordered: each leaves the device ready for the next.
# =========================================================================

def test_a_tour_shows_on_boot():
    """Tour overlay is visible after boot when tour_completed=False."""
    intro_text = _load_label("TOUR_INTRO", "en")[0]
    labels = find_labels_overlay()
    assert intro_text in labels, (
        f"Expected tour intro text in overlay. Got: {labels}"
    )


def test_b_no_prev_at_step_0():
    """On step 0 the prev button is a transparent placeholder with CLICKABLE removed.

    The widget exists (same nav layout as all steps) but is rendered invisible
    and has lv.obj.FLAG.CLICKABLE removed — the firmware contract tested here.
    """
    intro_text = _load_label("TOUR_INTRO", "en")[0]
    assert intro_text in find_labels_overlay(), "Precondition: must be on step 0"

    last_idx = _tour_overlay_content_idx()

    # Check CLICKABLE flag on nav child 0 (the prev placeholder).
    out2 = disco_run(
        "repl", "exec",
        f"import lvgl as lv; lt=lv.display_get_default().get_layer_top(); "
        f"w=lt.get_child(0); c=w.get_child({last_idx}); nav=c.get_child(1); "
        f"print(nav.get_child(0).has_flag(lv.obj.FLAG.CLICKABLE))",
    )
    result = out2.strip().splitlines()[-1] if out2.strip() else ""
    assert result == "False", (
        f"Expected prev placeholder to be non-clickable at step 0, got: {result!r}"
    )


def test_c_next_advances_prev_goes_back():
    """NEXT advances to step 1; PREV returns to step 0."""
    intro_text = _load_label("TOUR_INTRO", "en")[0]
    step1_text  = _load_label(STEP_KEYS[1], "en")[0]

    _click_tour_nav("next")
    assert step1_text in find_labels_overlay(), (
        f"Expected step 1 text after NEXT. Got: {find_labels_overlay()}"
    )

    _click_tour_nav("prev")
    assert intro_text in find_labels_overlay(), (
        f"Expected step 0 text after PREV. Got: {find_labels_overlay()}"
    )


def test_d_skip_dismisses_tour():
    """Clicking 'Skip Tour' hides the overlay and marks tour_completed=True."""
    skip_text = _load_label("TOUR_SKIP_BTN", "en")[0]
    click_overlay_by_label(skip_text)

    assert find_labels_overlay() == [], (
        f"Expected empty overlay after skip. Got: {find_labels_overlay()}"
    )
    assert _tour_completed(), "tour_completed should be True after skip"


def test_e_skipped_tour_persists_after_reset():
    """tour_completed=True survives a soft reset (overlay absent on reboot)."""
    soft_reset()
    ensure_main_menu()

    assert find_labels_overlay() == [], "Tour should not reappear after reset"
    assert _tour_completed(), "tour_completed should persist after reset"


def test_f_restart_tour_from_device_menu():
    """'Restart Tour' in Device Menu re-launches the intro overlay."""
    restart_label = _load_label("DEVICE_MENU_RESTART_TOUR", "en")[0]
    navigate_to_device_menu("en")
    click_by_label(restart_label)

    intro_text = _load_label("TOUR_INTRO", "en")[0]
    assert intro_text in find_labels_overlay(), (
        f"Expected tour intro after restart. Got: {find_labels_overlay()}"
    )


def test_g_all_steps_reachable_via_next():
    """All tour steps are accessible by walking NEXT from step 0 to the last."""
    # Precondition: on step 0 from test_f.
    for i, key in enumerate(STEP_KEYS):
        step_text = _load_label(key, "en")[0]
        labels = find_labels_overlay()
        assert step_text in labels, (
            f"Step {i} ({key}): expected {step_text!r} in overlay. Got: {labels}"
        )
        if i < len(STEP_KEYS) - 1:
            _click_tour_nav("next")


def test_h_complete_via_checkmark():
    """On the last step the skip button is a checkmark; clicking it completes the tour."""
    # Precondition: on the last step from test_g.
    _click_tour_nav("skip")

    assert find_labels_overlay() == [], (
        f"Expected empty overlay after checkmark. Got: {find_labels_overlay()}"
    )
    assert _tour_completed(), "tour_completed should be True after checkmark"


def test_i_completed_tour_persists_after_reset():
    """tour_completed=True survives a soft reset after completing the full tour."""
    soft_reset()
    ensure_main_menu()

    assert find_labels_overlay() == [], "Tour should not reappear after full completion"
    assert _tour_completed(), "tour_completed should persist after reset"
