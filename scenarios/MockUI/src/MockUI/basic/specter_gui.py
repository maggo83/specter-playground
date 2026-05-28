import lvgl as lv

try:  # only present on the f469 firmware build, not on the unix simulator
    import udisplay as _udisplay  # type: ignore
except ImportError:  # pragma: no cover
    _udisplay = None

# Anim-type IDs accepted by udisplay.transition() (must match the
# TFT_ANIM_* macros in f469-disco/usermods/udisplay_f469/lv_stm_hal/lv_stm_hal.h).
_HW_ANIM_HORIZONTAL_SLIDE_IN  = 1
_HW_ANIM_HORIZONTAL_SLIDE_OUT = 2
_HW_ANIM_HORIZONTAL_PUSH_IN   = 3
_HW_ANIM_HORIZONTAL_PUSH_OUT  = 4
_HW_ANIM_VERTICAL_SLIDE_IN    = 5
_HW_ANIM_VERTICAL_SLIDE_OUT   = 6

# Easing kind IDs (must match TFT_EASING_* in lv_stm_hal.h). The compositor
# applies the curve to the elapsed-time axis at each VBLANK tick to map
# linear time -> eased pixel offset. Pick one default here; the per-call
# site can override by passing `easing=` directly.
_HW_EASE_LINEAR            = 0
_HW_EASE_IN_CUBIC          = 1
_HW_EASE_OUT_CUBIC         = 2
_HW_EASE_IN_OUT_CUBIC      = 3
_HW_EASE_OUT_QUINT         = 4

# Default curve used by every HW transition unless the caller overrides
# it. Change this single line to retune the feel of the whole UI.
_HW_EASING_DEFAULT = _HW_EASE_IN_OUT_CUBIC

from .utils.ui_consts import SCREEN_HEIGHT, SCREEN_WIDTH, CONTENT_PCT, anim_duration_ms, GUI_REFRESH_MS, TITLE_ROW_HEIGHT
from ..stubs import DeviceState
from .ui_state import UIState, Context
from .i18n import I18nManager
from .tour import GuidedTour, INTRO_TOUR_STEPS
from .utils.keyboard_manager import KeyboardManager
from .utils.animations import slide_x, slide_y, GUIAnimations
from .components.navigation_bar import NavigationBar
from .components.dropup import DropUpState
from .components.app_screen import AppScreen
from .utils.ui_utils import configure_as_bare

_CONTENT_H = SCREEN_HEIGHT * CONTENT_PCT // 100


from .templates.action_screen import ActionScreen
from ..main_screens.main_menu import MainMenu
from ..main_screens.locked_menu import LockedMenu
from ..wallet_screens import (
    WalletMenu,
    ConnectWalletsMenu,
    AddWalletMenu,
    CreateCustomWalletMenu,
    ViewSignersMenu,
)
from ..seed_screens import (
    AddSeedMenu,
    SeedPhraseMenu,
    StoreSeedphraseMenu,
    ClearSeedphraseMenu,
    GenerateSeedMenu,
    PassphraseMenu,
    RelatedWalletsForSeedMenu,
)
from ..device_screens import (
    SecuritySettingsMenu,
    BackupsMenu,
    FirmwareMenu,
    InterfacesMenu,
    StorageMenu,
    SecurityFeaturesMenu,
    LanguageMenu,
    SettingsMenu,
    PreferencesMenu,
)


_VIEW_MAP = {
    "locked":                   LockedMenu,
    "main":                     MainMenu,
    "start_intro_tour":         MainMenu,
    "manage_wallet":            WalletMenu,
    "view_signers":             ViewSignersMenu,
    "manage_security_settings": SecuritySettingsMenu,
    "manage_backups":           BackupsMenu,
    "manage_firmware":          FirmwareMenu,
    "connect_sw_wallet":        ConnectWalletsMenu,
    "add_seed":                 AddSeedMenu,
    "add_wallet":               AddWalletMenu,
    "manage_security_features": SecurityFeaturesMenu,
    "interfaces":               InterfacesMenu,
    "manage_seedphrase":        SeedPhraseMenu,
    "related_wallets_for_seed": RelatedWalletsForSeedMenu,
    "store_seedphrase":         StoreSeedphraseMenu,
    "clear_seedphrase":         ClearSeedphraseMenu,
    "generate_seedphrase":      GenerateSeedMenu,
    "set_passphrase":           PassphraseMenu,
    "create_custom_wallet":     CreateCustomWalletMenu,
    "manage_storage":           StorageMenu,
    "select_language":          LanguageMenu,
    "manage_preferences":       PreferencesMenu,
    "manage_settings":          SettingsMenu,
}


class SpecterGui(lv.obj):

    def __init__(self, specter_state=None, ui_state=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_scroll_dir(lv.DIR.NONE)

        self.on_navigate = self.navigate_to

        # Initialize i18n manager
        self.i18n = I18nManager()

        if specter_state:
            self.device_state = specter_state
        else:
            self.device_state = DeviceState()

        if ui_state:
            self.ui_state = ui_state
        else:
            self.ui_state = UIState()

        self.keyboard_manager = KeyboardManager(self)
        self._animating = False   # True while a slide animation is running
        self._anim_refs = None    # holds Python callbacks + anim objects alive

        # Active screen (screen.view holds the active TitledScreen widget)
        self.screen = None

        # Build the initial screen for the current ui_state menu
        self.screen = self._make_screen()

        # Navigation bar at bottom — always present, owned by SpecterGui
        self.navigation_bar = NavigationBar(self)
        self.navigation_bar.align(lv.ALIGN.BOTTOM_MID, 0, 0)

        # Start guided tour on first startup (after UI is fully constructed)
        if self.ui_state.is_run_tour_on_startup:
            GuidedTour(self, GuidedTour.resolve_steps(INTRO_TOUR_STEPS, self)).start()

        # Periodic refresh (e.g. to update battery level)
        def _tick(timer):
            self.device_state.debug_cycle_battery()
            self.refresh_ui()
        lv.timer_create(_tick, GUI_REFRESH_MS, None)
        
        self.refresh_ui()

    def change_language(self, lang_code):
        """Change the active language."""
        self.i18n.set_language(lang_code)

    def refresh_ui(self):
        """Centralized refresh method for all UI components."""
        self.screen.refresh()
        self.navigation_bar.refresh()

    def navigate_to(self, target_menu_id=None, target_seed="unset", target_wallet="unset"):
        # Drop all input while animating
        if self._animating:
            return

        if target_menu_id == "locked":
            self.device_state.lock()
        if self.device_state.is_locked:
            target_menu_id = "locked"

        going_back = target_menu_id in [None, "back"]

        # Update UIState navigation history
        if going_back:
            anim = self.ui_state.pop_menu()
        elif target_menu_id in ["start_intro_tour", "main", "locked"]:
            anim = self.ui_state.clear_history()
            self.ui_state.current_menu_id = target_menu_id
        else:
            anim = self.ui_state.push_menu(target_menu_id)

        if target_seed != "unset":
            self.ui_state.set_active_seed(target_seed)
        if target_wallet != "unset":
            self.ui_state.set_active_wallet(target_wallet)

        if anim is not None and self.ui_state.are_animations_enabled:
            self._do_transition(anim)
        else:
            # Synchronously dismiss any open drop-up before rebuilding
            # the screen. Without an animation we have no chained close
            # path, so an open drop-up (and its backdrop) would otherwise
            # stay drawn on top of the new screen content.
            nav = getattr(self, "navigation_bar", None)
            if nav is not None:
                nav.close_dropups_sync()
            if self.screen:
                self.screen.delete()
            self.screen = self._make_screen()
            self.refresh_ui()

        if self.ui_state.current_menu_id == "start_intro_tour":
            self.ui_state.current_menu_id = "main"
            GuidedTour(self, GuidedTour.resolve_steps(INTRO_TOUR_STEPS, self)).start()

    def _make_screen(self):
        """Create a new AppScreen for the current ui_state and populate it with a view.

        Returns the new AppScreen.  Does NOT delete any old screen.
        """
        screen = AppScreen(self)
        screen.view = self._build_view(screen, self.ui_state.current_menu_id)
        return screen

    def _build_view(self, screen, menu_id):
        """Instantiate and return the correct view class for *menu_id* into *screen*."""
        class_name = _VIEW_MAP.get(menu_id)
        if class_name is not None:
            return class_name(screen)
        return ActionScreen(menu_id, screen)

    def _do_transition(self, anim_type):
        """Animate from the current screen to a freshly-built new screen.

        Dispatches to one of two cases:
          • Case 3 (within SEED/WALLET context, context bar stays): animate
            only the view widget horizontally inside ``screen.content``.
          • Cases 1/2 (between contexts, or context without bar): animate the
            entire Screen unit (bar + battery + content move together).
        """
        self._animating = True

        ctx = self.ui_state.active_context  # already updated by navigate_to
        ctx_has_bar = self.screen.context_bar is not None
        is_horizontal = anim_type in (
            GUIAnimations.horizontal_slide_in,
            GUIAnimations.horizontal_slide_out,
            GUIAnimations.horizontal_push_in,
            GUIAnimations.horizontal_push_out,
        )
        within_ctx_with_bar = (
            ctx_has_bar
            and is_horizontal
            and (ctx == Context.SEED or ctx == Context.WALLET)
        )

        if within_ctx_with_bar:
            # Phase 3: route within-context horizontal animations through
            # the HW compositor too -- the legacy LVGL slide on the view
            # widget is slow and tears against the live FB. On the unix
            # simulator (no udisplay) fall back to the legacy path.
            if _udisplay is not None and anim_type in self._hw_anim_table():
                self._transition_within_context_hw(anim_type)
            else:
                self._transition_within_context(anim_type)
        else:
            self._transition_full_screen(anim_type)

    def _transition_within_context(self, anim_type):
        """Case 3: slide only the view widget inside the existing screen.content."""
        old_screen = self.screen
        old_view = old_screen.view
        content = old_screen.content
        content_h = content.get_height()
        content.set_layout(lv.LAYOUT.NONE)
        old_view.set_pos(0, 0)
        old_view.set_size(SCREEN_WIDTH, content_h)

        # Build new view into the same screen (added to content as 2nd child)
        new_view = self._build_view(old_screen, self.ui_state.current_menu_id)
        old_screen.view = new_view
        new_view.set_size(SCREEN_WIDTH, content_h)

        anims = []
        W = SCREEN_WIDTH

        def _cleanup_case3():
            self._animating = False
            self._anim_refs = None
            old_view.delete()
            content.set_layout(lv.LAYOUT.FLEX)
            content.set_flex_flow(lv.FLEX_FLOW.COLUMN)
            self.refresh_ui()

        if anim_type == GUIAnimations.horizontal_slide_in:
            new_view.set_x(W)
            anims.append(slide_x(new_view, W, 0, anim_duration_ms(W),
                                on_done_cb=lambda a: _cleanup_case3()))
        elif anim_type == GUIAnimations.horizontal_slide_out:
            new_view.set_x(0)
            old_view.move_foreground()
            anims.append(slide_x(old_view, 0, W, anim_duration_ms(W),
                                on_done_cb=lambda a: _cleanup_case3()))

        for a in anims:
            a.start()
        self._anim_refs = anims

    def _transition_within_context_hw(self, anim_type):
        """Case 3 via HW compositor: slide only the view widget tear-free.

        The context bar (and battery / nav bar) stay outside the animation
        rect; the HW compositor seeds the outside-rect with the NEW frame
        and slides the view interior at 60 Hz with no LVGL CPU cost per
        frame.
        """
        hw_type = self._hw_anim_table()[anim_type]

        old_screen = self.screen
        old_view = old_screen.view
        content = old_screen.content
        content_h = content.get_height()
        content.set_layout(lv.LAYOUT.NONE)
        old_view.set_pos(0, 0)
        old_view.set_size(SCREEN_WIDTH, content_h)

        # Build new view into the same screen.
        new_view = self._build_view(old_screen, self.ui_state.current_menu_id)
        old_screen.view = new_view
        new_view.set_size(SCREEN_WIDTH, content_h)
        new_view.set_pos(0, 0)

        # Render the NEW frame into FB2: hide old_view so the offscreen
        # render produces a pure NEW composition (context bar + new_view).
        old_view.add_flag(lv.obj.FLAG.HIDDEN)
        self.invalidate()
        # Also invalidate layer_top so any modal/overlay re-renders into
        # FB2 above the new view.
        _disp = lv.display_get_default()
        _top = _disp.get_layer_top() if _disp is not None else None
        if _top is not None:
            _top.invalidate()

        # Animation rect = the content area, sandwiched between the
        # context bar (top TITLE_ROW_HEIGHT px) and the nav bar (below
        # _CONTENT_H). Both outside-rect strips are seeded with NEW.
        rect_y = TITLE_ROW_HEIGHT
        rect_h = _CONTENT_H - TITLE_ROW_HEIGHT

        def _on_done(_arg=None):
            self._animating = False
            self._anim_refs = None
            self._hw_anim_done_cb = None
            try:
                old_view.delete()
            except Exception:
                pass
            content.set_layout(lv.LAYOUT.FLEX)
            content.set_flex_flow(lv.FLEX_FLOW.COLUMN)
            # See _transition_full_screen_hw: skipped flushes during the
            # HW anim leave stale pixels for any LVGL state changes that
            # happened in parallel. Force a full re-render.
            _d = lv.display_get_default()
            _lt = _d.get_layer_top() if _d is not None else None
            if _lt is not None:
                _lt.invalidate()
            self.invalidate()
            self.refresh_ui()

        self._hw_anim_done_cb = _on_done
        # Travel distance: horizontal -> rect_w, vertical -> rect_h. Here the
        # rect is the content area between the context bar and the nav bar.
        if anim_type in (GUIAnimations.vertical_slide_in,
                         GUIAnimations.vertical_slide_out):
            dur_ms = anim_duration_ms(rect_h)
        else:
            dur_ms = anim_duration_ms(SCREEN_WIDTH)
        _udisplay.transition(hw_type, dur_ms,
                             0, rect_y, SCREEN_WIDTH, rect_h,
                             _on_done, _HW_EASING_DEFAULT)
        self._anim_refs = None
    # first use because GUIAnimations may be a class-level enum that
    # cannot be evaluated at module import time on the simulator.
    _HW_ANIM_TABLE = None

    @classmethod
    def _hw_anim_table(cls):
        if cls._HW_ANIM_TABLE is None:
            cls._HW_ANIM_TABLE = {
                GUIAnimations.horizontal_slide_in:  _HW_ANIM_HORIZONTAL_SLIDE_IN,
                GUIAnimations.horizontal_slide_out: _HW_ANIM_HORIZONTAL_SLIDE_OUT,
                GUIAnimations.horizontal_push_in:   _HW_ANIM_HORIZONTAL_PUSH_IN,
                GUIAnimations.horizontal_push_out:  _HW_ANIM_HORIZONTAL_PUSH_OUT,
                GUIAnimations.vertical_slide_in:    _HW_ANIM_VERTICAL_SLIDE_IN,
                GUIAnimations.vertical_slide_out:   _HW_ANIM_VERTICAL_SLIDE_OUT,
            }
        return cls._HW_ANIM_TABLE

    def _transition_full_screen_hw(self, anim_type):
        """Hardware-compositor transition for all 6 animation types.

        Build new_screen, force a full LVGL refresh into FB2 (offscreen),
        then ask `udisplay.transition` to slide OLD (currently live FB)
        and NEW (FB2) tear-free at 60 Hz with no LVGL CPU cost per frame.
        Completion is reported via a scheduled Python callback which
        deletes old_screen and finalises navigation state.
        """
        hw_type = self._hw_anim_table()[anim_type]

        old_screen = self.screen
        new_screen = self._make_screen()
        self.screen = new_screen

        # Position new screen on top of old at (0,0). Both are children of
        # SpecterGui. Hide old so the offscreen LVGL render produces a
        # pure NEW frame. Force a full-screen invalidate so lv_refr_now
        # repaints every pixel into FB2 (without invalidate it would only
        # repaint the dirty regions caused by adding new_screen / hiding
        # old_screen).
        new_screen.set_pos(0, 0)
        old_screen.add_flag(lv.obj.FLAG.HIDDEN)
        # Update the navigation bar to reflect the NEW screen's active
        # icon state BEFORE the offscreen FB2 render, otherwise NEW is
        # captured with the OLD navbar highlight and the icon appears
        # to "flip" only at the end of the animation. (Vertical
        # animations were not affected because their callers update
        # the navbar state synchronously when opening/closing the
        # dropup; horizontal anims rely solely on refresh_ui.)
        self.navigation_bar.refresh()
        self.navigation_bar.move_foreground()
        # CRITICAL for vertical_slide_in chained after a dropup close:
        # the ContextBar widgets built inside AppScreen.__init__ render
        # as BLANK in the offscreen FB2 capture (children are present
        # but their pixels are missing). The post-anim refresh_ui()
        # rebuilds the bar via ContextBar.refresh() which does
        # delete_all_children_of + _build, and THAT render does land
        # correctly on the live FB -- which is why the bar "pops in"
        # only after the slide. Run the same refresh path now so the
        # offscreen FB2 capture includes the bar pixels.
        try:
            new_screen.refresh()
        except Exception:
            pass
        # Force LVGL to run a layout/style pass on the freshly created
        # new_screen tree NOW so the dirty regions cover the final
        # widget positions.
        try:
            new_screen.update_layout()
        except Exception:
            pass
        # Now invalidate the whole composition so the dirty list
        # covers every pixel the offscreen render must produce.
        self.invalidate()
        # Belt-and-suspenders: also invalidate the new_screen and its
        # context_bar / battery sub-widgets directly so even if a
        # parent-level invalidate were collapsed, the bar area is
        # guaranteed dirty in FB2.
        try:
            new_screen.invalidate()
            if getattr(new_screen, "context_bar", None) is not None:
                new_screen.context_bar.invalidate()
            if getattr(new_screen, "battery", None) is not None:
                new_screen.battery.invalidate()
        except Exception:
            pass
        # Also invalidate layer_top so any active modal/overlay (e.g. a
        # dropup panel + dim backdrop) is re-rendered ABOVE the new
        # screen into FB2. Without this, layer_top isn't marked dirty
        # and lv_refr_now leaves FB2 without the overlay -- causing
        # the context bar of NEW to appear undimmed during slide-in.
        _disp = lv.display_get_default()
        _top = _disp.get_layer_top() if _disp is not None else None
        if _top is not None:
            _top.invalidate()

        def _on_hw_transition_done(_arg=None):
            # Called via mp_sched_schedule from the LTDC reload IRQ once
            # the final t=1.0 frame is on the panel. Defer all heavy
            # cleanup to a one-shot LVGL timer so we exit the schedule
            # callback context immediately. Running widget deletion +
            # refresh_ui directly here interacts poorly with the
            # vertical-slide-in tail (device freezes silently for that
            # case only); deferring fixes it without affecting the
            # horizontal paths.
            self._animating = False
            self._hw_anim_done_cb = None

            def _do_cleanup(timer):
                try:
                    timer.delete()
                except Exception:
                    pass
                try:
                    self._anim_refs = None
                except Exception:
                    pass
                try:
                    print("[hw_anim_done] start cleanup")
                except Exception:
                    pass
                try:
                    old_screen.delete()
                except Exception as e:
                    try: print("[hw_anim_done] old_screen.delete failed:", e)
                    except Exception: pass
                try:
                    self.navigation_bar._release_backdrop_if_idle()
                except Exception as e:
                    try: print("[hw_anim_done] release_backdrop failed:", e)
                    except Exception: pass
                try:
                    self.navigation_bar.move_foreground()
                except Exception as e:
                    try: print("[hw_anim_done] move_foreground failed:", e)
                    except Exception: pass
                try:
                    _d = lv.display_get_default()
                    _lt = _d.get_layer_top() if _d is not None else None
                    if _lt is not None:
                        _lt.invalidate()
                    self.invalidate()
                except Exception as e:
                    try: print("[hw_anim_done] invalidate failed:", e)
                    except Exception: pass
                try:
                    self.refresh_ui()
                except Exception as e:
                    try: print("[hw_anim_done] refresh_ui failed:", e)
                    except Exception: pass
                try:
                    print("[hw_anim_done] cleanup OK")
                except Exception:
                    pass

            try:
                t = lv.timer_create(_do_cleanup, 1, None)
                t.set_repeat_count(1)
            except Exception:
                # Fallback: run inline if timer_create fails.
                _do_cleanup(None)

        # Keep a strong reference so the GC cannot reap the callable
        # while it is queued by mp_sched_schedule.
        self._hw_anim_done_cb = _on_hw_transition_done

        # Travel distance: horizontal moves the rect by its full width,
        # vertical by its full height. Here the rect is the whole content
        # area (0, 0, SCREEN_WIDTH, _CONTENT_H).
        if anim_type in (GUIAnimations.vertical_slide_in,
                         GUIAnimations.vertical_slide_out):
            dur_ms = anim_duration_ms(_CONTENT_H)
        else:
            dur_ms = anim_duration_ms(SCREEN_WIDTH)
        _udisplay.transition(hw_type, dur_ms,
                             0, 0, SCREEN_WIDTH, _CONTENT_H,
                             _on_hw_transition_done, _HW_EASING_DEFAULT)
        # No LVGL animations to register; compositor drives everything.
        self._anim_refs = None

    def _hw_dropup_slide_out(self, on_done):
        """Phase 1: HW slide the dropup panel(s) down behind the navbar.

        - Snap-delete dropup panels from the LVGL tree (keep the dim
          backdrop overlay so NEW retains the dimmed look).
        - Render NEW = current screen + overlay + navbar (no dropup)
          into FB2.
        - Run HW vertical_slide_out on the content rect: OLD (live FB)
          has the dropup over the whole content area, NEW underneath
          is the same screen + overlay -- the dropup pixels translate
          down behind the navbar while the bg stays put.
        - When the slide completes, call `on_done()`.

        Does NOT swap screens. Does NOT dispose the overlay (the
        chained phase 2, if any, will).
        """
        nav = self.navigation_bar

        # Compute the visible sub-rect (union over any open dropups)
        # BEFORE snap-deleting, so HW only translates the panel pixels
        # and not the dim area above them. The panel container is
        # _PANEL_MAX_H tall but actually slides up to panel_y = max_h -
        # panel_h, so the visible card area is (0, panel_y, W, panel_h).
        rect_y_top = _CONTENT_H
        rect_y_bot = 0
        for du in (nav._seed_dropup, nav._wallet_dropup):
            if du._panel is None:
                continue
            try:
                py = du._panel.get_y()
            except Exception:
                py = 0
            if py < rect_y_top:
                rect_y_top = py
            if _CONTENT_H > rect_y_bot:
                rect_y_bot = _CONTENT_H

        if rect_y_bot <= rect_y_top:
            # No open dropup found — caller bug, just invoke on_done.
            on_done()
            return

        rect_y = rect_y_top
        rect_h = rect_y_bot - rect_y_top

        for du in (nav._seed_dropup, nav._wallet_dropup):
            if du._panel is None:
                continue
            # CRITICAL: explicitly delete any LV animation targeting
            # the panel BEFORE deleting the panel widget. A row tap
            # inside the dropup calls self.close() which starts a
            # slide_y LV anim on the panel, then immediately triggers
            # navigation (which routes here). If we delete the panel
            # without removing the anim first, the anim's per-tick
            # exec_cb (panel.set_y) fires on freed memory -> HardFault
            # (LEDs flash). lv.anim_delete(panel, None) removes all
            # anims targeting `panel` regardless of exec_cb.
            try:
                lv.anim_delete(du._panel, None)
            except Exception:
                pass
            try:
                du._panel.delete()
            except Exception:
                pass
            du._panel = None
            du._anim = None
            du._animating = False
            du._closing = False

        # Re-invalidate everything (incl. top layer for the overlay)
        # so the offscreen FB2 render captures the post-snap state.
        self.invalidate()
        _disp = lv.display_get_default()
        _top = _disp.get_layer_top() if _disp is not None else None
        if _top is not None:
            _top.invalidate()

        def _on_phase1_done(_arg=None):
            self._hw_anim_done_cb = None
            self._animating = False
            on_done()

        self._animating = True
        self._hw_anim_done_cb = _on_phase1_done
        # Travel distance = panel slide height (capped at content height).
        _udisplay.transition(_HW_ANIM_VERTICAL_SLIDE_OUT, anim_duration_ms(rect_h),
                             0, rect_y, SCREEN_WIDTH, rect_h,
                             _on_phase1_done, _HW_EASING_DEFAULT)

    def _hw_dropup_slide_in(self, dropup, container, on_done=None):
        """HW slide a dropup panel UP into view (vertical_slide_in).

        - Ensure the dim backdrop overlay is in the live FB by forcing
          a synchronous LVGL refresh BEFORE building the panel. Without
          this, OLD inside the slide-in sub-rect would show
          un-dimmed bg while the panel rises -- a visible glitch above
          the moving panel.
        - Build the panel at its FINAL on-screen position (snap_open).
        - Render NEW = bg + overlay + panel into FB2.
        - Run HW vertical_slide_in on the panel sub-rect: NEW (panel)
          slides up from below into the sub-rect; OLD sub-rect stays
          as bg + overlay (already in live FB).
        - On completion: ``on_done()`` (if given) plus a navbar refresh.
        """
        _disp = lv.display_get_default()
        # Force LVGL to flush the freshly-created backdrop overlay into
        # the live FB so the OLD sub-rect shows bg+overlay (not bare bg)
        # while the panel slides up.
        try:
            lv.refr_now(_disp)
        except Exception:
            pass

        rect = dropup.snap_open(container)
        if rect is None:
            # Drop-up already open/animating — nothing to do.
            if on_done is not None:
                on_done()
            return
        rect_x, rect_y, rect_w, rect_h = rect

        # Invalidate everything so the offscreen FB2 render captures
        # bg + overlay + panel together.
        self.invalidate()
        _top = _disp.get_layer_top() if _disp is not None else None
        if _top is not None:
            _top.invalidate()

        def _on_open_done(_arg=None):
            self._hw_anim_done_cb = None
            self._animating = False
            try:
                self.navigation_bar.refresh()
            except Exception:
                pass
            if on_done is not None:
                on_done()

        self._animating = True
        self._hw_anim_done_cb = _on_open_done
        # Travel distance = panel slide height (capped at content height).
        _udisplay.transition(_HW_ANIM_VERTICAL_SLIDE_IN, anim_duration_ms(rect_h),
                             rect_x, rect_y, rect_w, rect_h,
                             _on_open_done, _HW_EASING_DEFAULT)

    def _hw_dropup_close_pure(self, on_done=None):
        """HW slide the open dropup(s) down; no chained screen change.

        Wraps `_hw_dropup_slide_out` and disposes the dim backdrop in
        its on-done callback, since there is no phase 2 to do it.
        """
        def _after_slide():
            try:
                self.navigation_bar._release_backdrop_if_idle()
            except Exception:
                pass
            try:
                self.refresh_ui()
            except Exception:
                pass
            if on_done is not None:
                on_done()

        self._hw_dropup_slide_out(_after_slide)

    def _close_dropups_then(self, anim_type):
        """Two-phase HW: slide dropup down, then run the screen transition.

        Phase 1 = HW vertical_slide_out of the dropup. As soon as phase
        1 completes we dispose the dim backdrop overlay and force a
        synchronous LVGL flush so the live FB shows the undimmed bg
        BEFORE phase 2 starts. Phase 2 = HW screen transition via
        ``_transition_full_screen_hw`` -- its NEW is rendered without
        the overlay, so the new screen slides in already undimmed.
        """
        nav = self.navigation_bar
        has_open_dropup = any(
            du._panel is not None
            for du in (nav._seed_dropup, nav._wallet_dropup)
        )
        if not has_open_dropup:
            self._transition_full_screen_hw(anim_type)
            return

        def _after_phase1():
            # Dispose the dim backdrop overlay so it is gone for phase 2.
            try:
                nav._release_backdrop_if_idle()
            except Exception:
                pass
            # Force LVGL to flush the now-overlay-less state to the
            # live FB so phase 2's OLD shows undimmed bg from t=0.
            try:
                _disp = lv.display_get_default()
                _top = _disp.get_layer_top() if _disp is not None else None
                if _top is not None:
                    _top.invalidate()
                lv.refr_now(_disp)
            except Exception:
                pass
            self._transition_full_screen_hw(anim_type)

        self._hw_dropup_slide_out(_after_phase1)

    def _transition_full_screen(self, anim_type):
        """Cases 1/2: slide the entire Screen unit (bar + content) via a clip container."""
        # Phase 3: route ALL 6 animation types through the LTDC/DMA2D
        # compositor when running on hardware. The compositor renders the
        # new screen offscreen into FB2 and then composes OLD->NEW
        # tear-free at 60 Hz, completely bypassing per-frame LVGL
        # re-rendering of the moving widgets. On the unix simulator
        # (udisplay not available) we fall through to the legacy path.
        #
        # If a dropup is currently open, chain two HW transitions: first
        # close the dropup (vertical_slide_out of the panel + dim
        # backdrop), then run the requested screen transition. This way
        # both phases remain tear-free and the dropup vanishes before
        # the new screen slides in -- which the single-rectangle
        # compositor cannot do in parallel.
        nav = getattr(self, "navigation_bar", None)
        dropup_open = (nav is not None
                       and getattr(nav, "_backdrop", None) is not None)

        if (_udisplay is not None
                and anim_type in self._hw_anim_table()):
            if dropup_open:
                self._close_dropups_then(anim_type)
            else:
                self._transition_full_screen_hw(anim_type)
            return

        # Legacy LV path (no HW compositor available, e.g. unix
        # simulator). We cannot chain an HW slide-out for the dropup,
        # so dismiss it synchronously before swapping screens.
        if dropup_open and nav is not None:
            nav.close_dropups_sync()

        old_screen = self.screen
        new_screen = self._make_screen()
        self.screen = new_screen

        # temporary clip container: same size as the content zone
        # (480×_CONTENT_H).
        # Both screens are reparented into it so LVGL's default parent-clip
        # prevents them from ever painting over the navigation bar below.
        anim_clip = lv.obj(self)
        configure_as_bare(anim_clip, width=SCREEN_WIDTH, height=_CONTENT_H,
                           transparent_bg=True)
        anim_clip.set_pos(0, 0)
        anim_clip.set_layout(lv.LAYOUT.NONE)
        anim_clip.set_scroll_dir(lv.DIR.NONE)

        # Reparent both screens; their coords were (0,0) relative to
        # SpecterGui which is identical to (0,0) inside anim_clip.
        old_screen.set_parent(anim_clip)
        old_screen.set_pos(0, 0)
        new_screen.set_parent(anim_clip)
        new_screen.set_pos(0, 0)

        # Navigation bar must remain above the clip container.
        self.navigation_bar.move_foreground()

        def _cleanup_whole():
            self._animating = False
            self._anim_refs = None
            # Reparent new_screen back to SpecterGui before deleting the
            # clip (which would otherwise take new_screen with it).
            new_screen.set_parent(self)
            new_screen.set_pos(0, 0)
            anim_clip.delete()   # also deletes old_screen
            self.navigation_bar.move_foreground()
            self.refresh_ui()

        anims = []
        W = SCREEN_WIDTH

        if anim_type == GUIAnimations.horizontal_slide_in:
            anims.append(slide_x(new_screen, W, 0, anim_duration_ms(W),
                                on_done_cb=lambda a: _cleanup_whole()))
        elif anim_type == GUIAnimations.horizontal_slide_out:
            old_screen.move_foreground()   # old on top within anim_clip
            anims.append(slide_x(old_screen, 0, W, anim_duration_ms(W),
                                on_done_cb=lambda a: _cleanup_whole()))
        elif anim_type == GUIAnimations.horizontal_push_in:
            anims.append(slide_x(new_screen, W, 0, anim_duration_ms(W)))
            anims.append(slide_x(old_screen, 0, -W, anim_duration_ms(W),
                                on_done_cb=lambda a: _cleanup_whole()))
        elif anim_type == GUIAnimations.horizontal_push_out:
            anims.append(slide_x(new_screen, -W, 0, anim_duration_ms(W)))
            anims.append(slide_x(old_screen, 0, W, anim_duration_ms(W),
                                on_done_cb=lambda a: _cleanup_whole()))
        elif anim_type == GUIAnimations.vertical_slide_in:
            anims.append(slide_y(new_screen, _CONTENT_H, 0, anim_duration_ms(_CONTENT_H),
                                on_done_cb=lambda a: _cleanup_whole()))
        elif anim_type == GUIAnimations.vertical_slide_out:
            old_screen.move_foreground()   # old on top within anim_clip
            anims.append(slide_y(old_screen, 0, _CONTENT_H, anim_duration_ms(_CONTENT_H),
                                on_done_cb=lambda a: _cleanup_whole()))

        for a in anims:
            a.start()
        self._anim_refs = anims
