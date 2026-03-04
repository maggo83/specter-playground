"""Fixtures for device integration tests using the disco tool.

The disco tool lives outside this repo for now.  Update DISCO_SCRIPT
when it is merged into the main branch.

Requirements:
  - STM32F469 Discovery board connected via USB
  - disco tool dependencies installed in the active venv (mpremote, click, pyserial)

By default these tests build the MockUI firmware with German included
(ADD_LANG=de) and flash it before running.  Pass --no-build-flash to skip
this step if you have already flashed a suitable binary yourself.
"""
import json
import os
import subprocess
import sys
import time

import pytest

# =========================================================================
# Path to the disco CLI script.
# TODO: Update this once disco is merged into specter-playground.
# =========================================================================
DISCO_SCRIPT = os.environ.get(
    "DISCO_SCRIPT",
    "/home/marco/DATA/01_Texte/BitCoin/Specter/f469-disco_disco_tool/scripts/disco",
)

# Firmware output path produced by ``make mockui``.
_FIRMWARE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "bin", "mockui.bin"
)
# Repo root (three levels up from tests_device/)
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Run through sys.executable so the test venv (with mpremote etc.) is used.
_CMD = [sys.executable, DISCO_SCRIPT]

# =========================================================================
# Language label loading — single source of truth from the JSON files.
# =========================================================================
_LANG_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "scenarios", "MockUI", "src", "MockUI", "i18n", "languages",
))

def _supported_lang_codes() -> list[str]:
    """Return all language codes found in the language JSON directory."""
    codes = []
    for name in sorted(os.listdir(_LANG_DIR)):
        if name.startswith("specter_ui_") and name.endswith(".json"):
            codes.append(name[len("specter_ui_"):-len(".json")])
    return codes


def _load_metadata(key: str, *lang_codes: str) -> tuple[str, ...]:
    """Return the *_metadata* value for *key* from each requested language file."""
    results = []
    for lang in lang_codes:
        path = os.path.join(_LANG_DIR, f"specter_ui_{lang}.json")
        try:
            with open(path) as f:
                data = json.load(f)
            v = data.get("_metadata", {}).get(key)
            if v:
                results.append(v)
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            pass
    return tuple(results)


def _load_label(key: str, *lang_codes: str) -> tuple[str, ...]:
    """Return the translated text for *key* from each requested language file.

    Unknown keys or missing files are silently skipped so the tuple always
    contains only real strings.
    """
    results = []
    for lang in lang_codes:
        path = os.path.join(_LANG_DIR, f"specter_ui_{lang}.json")
        try:
            with open(path) as f:
                data = json.load(f)
            v = data.get("translations", {}).get(key)
            if v is not None:
                text = v.get("text", v) if isinstance(v, dict) else v
                if text:
                    results.append(text)
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            pass
    return tuple(results)



def pytest_addoption(parser):
    parser.addoption(
        "--no-build-flash",
        action="store_true",
        default=False,
        help=(
            "Skip the build + flash step. Use only if you have already flashed "
            "a MockUI binary that includes the German language pack (ADD_LANG=de)."
        ),
    )


def disco_run(*args: str, timeout: int = 15, retries: int = 2) -> str:
    """Run ``disco <args>``, assert exit-code 0, return stripped stdout.

    Retries on transient serial errors (OSError, I/O error).
    """
    last_result = None
    for attempt in range(1 + retries):
        result = subprocess.run(
            [*_CMD, *args],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        # Retry on transient serial errors (various messages from pyserial/mpremote)
        err = result.stderr
        if any(s in err for s in ("OSError", "Input/output error", "Serial error",
                                   "readiness to read", "device disconnected")):
            last_result = result
            time.sleep(3)
            continue
        last_result = result
        break
    assert last_result.returncode == 0, (
        f"disco {' '.join(args)} failed (rc={last_result.returncode}):\n"
        f"stdout: {last_result.stdout}\nstderr: {last_result.stderr}"
    )
    return last_result.stdout.strip()


def find_labels() -> list[str]:
    """Return all visible text labels (len > 1) from the LVGL widget tree."""
    tree = json.loads(disco_run("ui", "screen", "--json"))
    labels = []

    def _walk(node):
        text = node.get("text")
        if text and len(text) > 1:
            labels.append(text)
        for child in node.get("children", []):
            _walk(child)

    for node in (tree if isinstance(tree, list) else [tree]):
        _walk(node)
    return labels


def go_back(delay: float = 1.0):
    """Click the back button (top-left, index 1.0.0) and wait.

    Returns True on success, False if the click failed (no back button).
    """
    result = subprocess.run(
        [*_CMD, "ui", "click", "--index", "1.0.0"],
        capture_output=True, text=True, timeout=15,
    )
    time.sleep(delay)
    return result.returncode == 0


def _wait_for_device_responsive(
    wait: float = 30.0,
    settle: float = 5.0,
    poll_interval: float = 3.0,
) -> None:
    """Poll until the device is responsive to REPL commands, or timeout."""
    deadline = time.monotonic() + wait
    time.sleep(settle)  # initial wait for device to finish booting
    while time.monotonic() < deadline:
        result = subprocess.run(
            [*_CMD, "repl", "exec", "print('pytest-alive')"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and "pytest-alive" in result.stdout:
            return
        time.sleep(poll_interval)
    raise RuntimeError(f"Device did not become responsive within {settle + wait}s")


def soft_reset(wait: float = 12.0):
    """Soft-reset the device and wait for it to be responsive again.

    ``disco repl reset`` sends Ctrl-C + Ctrl-D over pyserial.  The device
    reboots (USB disconnects/reconnects), so the command *always* exits
    with rc=1 and a "Serial error" — that is expected and ignored.
    """
    # Fire-and-forget: the serial error is expected because USB disconnects.
    subprocess.run(
        [*_CMD, "repl", "reset"],
        capture_output=True, text=True, timeout=10,
    )
    _wait_for_device_responsive(wait=wait)


def ensure_main_menu(max_depth: int = 5):
    """Navigate back until we're on the main menu.

    Tries go_back() repeatedly.  If the UI is unreachable or go_back()
    fails, falls back to a soft reset (Ctrl-D, USB reconnect).
    """
    main_menu_markers = _load_label("MAIN_MENU_TITLE", *_supported_lang_codes())
    for _ in range(max_depth):
        try:
            labels = find_labels()
        except (AssertionError, json.JSONDecodeError):
            # UI command failed — device may still be booting after a reset.
            time.sleep(3)
            continue
        if any(t in labels for t in main_menu_markers):
            return
        if not go_back():
            # No back button — soft reset to get to a clean main menu.
            soft_reset()
            continue

    # Final check after exhausting retries.
    labels = find_labels()
    assert any(t in labels for t in main_menu_markers), (
        f"Could not navigate to main menu. Labels: {labels}"
    )


def click_by_label(label: str, delay: float = 1.0) -> None:
    """Assert *label* is visible on the main screen and click it."""
    labels = find_labels()
    assert label in labels, f"Cannot find button {label!r}. Visible labels: {labels}"
    disco_run("ui", "click", label)
    time.sleep(delay)


def click_by_index(index_str: str, delay: float = 1.0) -> None:
    """Click a widget on the main screen by dot-separated tree index (e.g. '1.0.2')."""
    disco_run("ui", "click", "--index", index_str)
    time.sleep(delay)


def find_labels_overlay() -> list[str]:
    """Return all visible text labels (len > 1) from the LVGL layer_top (overlays)."""
    raw = disco_run("ui", "screen", "--layer", "top", "--json")
    if not raw:
        return []
    tree = json.loads(raw)
    labels = []

    def _walk(node):
        text = node.get("text")
        if text and len(text) > 1:
            labels.append(text)
        for child in node.get("children", []):
            _walk(child)

    for node in (tree if isinstance(tree, list) else [tree]):
        _walk(node)
    return labels


def click_overlay_by_label(label: str, delay: float = 1.0) -> None:
    """Assert *label* is visible in the overlay and click it."""
    labels = find_labels_overlay()
    assert label in labels, (
        f"Cannot find overlay button {label!r}. Visible overlay labels: {labels}"
    )
    disco_run("ui", "click", "--layer", "top", label)
    time.sleep(delay)


def click_overlay_by_index(index_str: str, delay: float = 1.0) -> None:
    """Click an overlay widget by dot-separated tree index (e.g. '0.1.2').

    Useful for icon-only buttons (prev/next/checkmark) that have no text label.
    """
    disco_run("ui", "click", "--layer", "top", "--index", index_str)
    time.sleep(delay)


def _read_flash_json(path: str) -> dict:
    """Read a JSON file from the device flash via REPL and return parsed dict."""
    output = disco_run(
        "repl", "exec",
        f"import json; f=open({path!r}); print(json.dumps(json.load(f))); f.close()",
    )
    return json.loads(output)


def navigate_to_language_menu(lang: str) -> None:
    """Navigate from the main menu to the language selection menu.

    *lang* is the language code currently active on the device (e.g. "en", "de").
    Button labels are resolved from the language JSON files.
    """
    ensure_main_menu()
    click_by_label(_load_label("MENU_MANAGE_SETTINGS", lang)[0])
    click_by_label(_load_label("MENU_MANAGE_DEVICE",   lang)[0])
    click_by_label(_load_label("MENU_LANGUAGE",        lang)[0])


def navigate_to_device_menu(lang: str = "en") -> None:
    """Navigate from the main menu to the Device settings menu.

    *lang* is the language code currently active on the device (e.g. "en", "de").
    """
    ensure_main_menu()
    click_by_label(_load_label("MENU_MANAGE_SETTINGS", lang)[0])
    click_by_label(_load_label("MENU_MANAGE_DEVICE",   lang)[0])


def ensure_english() -> None:
    """Ensure the device UI is in English, switching if needed.

    Detects the current language from visible main-menu labels and, if not
    English, navigates to the language menu and selects English.
    """
    ensure_main_menu()
    en_title = _load_label("MAIN_MENU_TITLE", "en")[0]
    if en_title in find_labels():
        return
    # Identify the current language and navigate accordingly.
    for lang in _supported_lang_codes():
        if lang == "en":
            continue
        if _load_label("MAIN_MENU_TITLE", lang)[0] in find_labels():
            navigate_to_language_menu(lang)
            click_by_label(_load_metadata("language_name", "en")[0])
            time.sleep(2)
            ensure_main_menu()
            return
    raise RuntimeError(f"Cannot determine current UI language. Labels: {find_labels()}")


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture(scope="session", autouse=True)
def _require_device(request):
    """Build firmware with German, flash it, then verify the board is reachable.

    The build+flash step is skipped only when --no-build-flash is passed.
    """
    if not request.config.getoption("--no-build-flash"):
        print("\n[device-tests] Building MockUI firmware with ADD_LANG=de ...")
        subprocess.run(
            ["nix", "develop", "-c", "make", "mockui", "ADD_LANG=de"],
            cwd=_REPO_ROOT,
            check=True,
        )
        print("[device-tests] Flashing firmware (blocking until done) ...")
        subprocess.run(
            [*_CMD, "flash", "program", os.path.abspath(_FIRMWARE)],
            check=True,
        )
        # Flash is complete. The board resets automatically at end of flashing.
        # Poll until MicroPython is responsive (up to 30s) rather than fixed sleep.
        print("[device-tests] Flash done — polling until board is responsive ...")

    # Always wait for the device to be responsive (covers both the build/flash
    # path and --no-build-flash with a freshly-flashed or already-running board).
    _wait_for_device_responsive(wait=60, settle=45, poll_interval=5)

    # Navigate to main menu and ensure English — device may be in any state
    # from a previous (possibly failed) run.
    ensure_main_menu()
    ensure_english()
    yield
