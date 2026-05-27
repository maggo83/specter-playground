# Animation Performance Optimization Plan

Phased plan to improve MockUI animation fluidity on STM32F469 Discovery hardware.
After each step we stop, build, flash, and verify on device.

Build: `nix develop --command bash -c "cmake ADD_LANG=de mockui"` (or current `make mockui` flow)
Flash: `/home/marco/DATA/01_Texte/BitCoin/Specter/f469-disco_disco_tool/scripts/disco flash program /home/marco/DATA/01_Texte/BitCoin/Specter/specter-playground/bin/mockui.bin --addr 0x08000000`

---

## Phase 1.1 — DMA2D Non-Blocking + Batched 2D Transfer

**Goal:** Replace 30 line-by-line blocking DMA2D transfers with **1 batched non-blocking 2D transfer per flush**.

### Changes
- **File:** `f469-disco/usermods/udisplay_f469/BSP_DISCO_F469NI/Drivers/BSP/STM32469I-Discovery/stm32469i_discovery_lcd.c`
  - Add new function `LL_ConvertBlockToARGB8888(src, dst, width, height, srcLineOffset, dstLineOffset, InputColorMode)` that issues **one** DMA2D 2D transfer (`hdma2d.Init.OutputOffset` + `LayerCfg.InputOffset` + `HAL_DMA2D_Start` with `xSize=width, ySize=height`).
  - Add IRQ-mode variant `LL_ConvertBlockToARGB8888_IT(...)` using `HAL_DMA2D_Start_IT`.
  - New `BSP_LCD_DrawBitmapRaw_IT(...)` that calls IRQ variant.
- **File:** `f469-disco/usermods/udisplay_f469/lv_stm_hal/lv_stm_hal.c`
  - `tft_flush` calls `BSP_LCD_DrawBitmapRaw_IT` instead of blocking variant.
  - Store the active `lv_display_t *` in a static so the IRQ handler can call `lv_display_flush_ready`.
  - Provide `tft_dma2d_xfer_cplt_cb()` callback to be wired into DMA2D HAL.
- **File:** `f469-disco/usermods/udisplay_f469/lv_stm_hal/lv_stm_hal.c` (or BSP)
  - Implement / hook `DMA2D_IRQHandler` (forward to `HAL_DMA2D_IRQHandler`).
  - Register `XferCpltCallback` on the DMA2D handle; callback signals LVGL.
  - Enable `DMA2D_IRQn` in NVIC (priority below SysTick).

### Validation
- Boot must work, no crashes.
- Visual: full screens still render correctly.
- Instrumentation: existing flush_stats should show **avg flush time drop by ~50×**.
- Expected FPS during animation: bumped from ~10-15 to ~25-30.

### Risk
- IRQ vs. main-context race in LVGL flush_ready — mitigated: LVGL v9 supports calling `lv_display_flush_ready` from ISR if `LV_USE_OS=0` (our case).
- DMA2D priority vs. LTDC: keep DMA2D IRQ at a priority that does not preempt SysTick.

---

## Phase 1.2 — RGB565 Source Buffer + DMA2D Format Conversion

**Goal:** Halve draw-buffer memory bandwidth; LVGL renders 16bpp, DMA2D converts RGB565→ARGB8888 on the fly.

### Changes
- **File:** `f469-disco/usermods/udisplay_f469/lv_stm_hal/lv_stm_hal.c`
  - Change `buf1` from `lv_color_t` (32bpp) to `uint16_t` array sized for **480×60 lines** (still ~57 KB).
  - Call `lv_display_set_color_format(disp, LV_COLOR_FORMAT_RGB565)`.
  - Pass `CM_RGB565` as input color mode to BSP draw call.
- **File:** `f469-disco/usermods/udisplay_f469/lv_conf.h`
  - Confirm `LV_COLOR_DEPTH 16` is acceptable for partial render (LVGL v9 supports per-display format independent of compile-time depth).
- **File:** `stm32469i_discovery_lcd.c`
  - `LL_ConvertBlockToARGB8888` already accepts `InputColorMode` — verify `CM_RGB565` path correct (sets DMA2D to actually convert).

### Validation
- Colors look correct (no swapped R/B channels).
- avg LVGL render time should drop ~30-40%.
- Combined with 1.1: animation should now hit consistent 30 FPS.

### Risk
- LVGL render path uses 16bpp internally — touch handling, font rendering must verify visually.
- DMA2D actually does work (conversion is real this time) — slightly slower DMA2D but still tiny.

---

## Phase 2 — SDRAM Double-Buffered Framebuffer + VSYNC Flip

**Goal:** Eliminate tearing, decouple from Python sleep jitter.

### Changes
- **File:** `stm32469i_discovery_lcd.c` (or BSP header)
  - Allocate two framebuffers in SDRAM: `LCD_FB_A = 0xC0000000`, `LCD_FB_B = 0xC0200000`.
  - Track `front_fb` / `back_fb` pointers.
- **File:** `lv_stm_hal.c`
  - `tft_flush` writes to **back** framebuffer.
  - On LVGL's last flush of a frame (`disp->flushing_last`), arm a "swap pending" flag.
- **File:** LTDC HAL hook
  - Implement `LTDC_IRQHandler` (or use STM32 HAL's line-event callback).
  - On VSYNC (LINE event at line 0): if swap pending → `HAL_LTDC_SetAddress(&hltdc, back_fb, layer)`; swap pointers; signal "frame_done".
- **File:** `scenarios/mockui_fw/main.py` and/or `display.c`
  - Expose `display.wait_vsync()` to Python.
  - Main loop becomes: `display.update_when_ready()` then wait for vsync semaphore instead of fixed `sleep_ms(30)`.
- **File:** `f469-disco/usermods/udisplay_f469/display.c`
  - Add Python-visible function to wait on vsync semaphore (e.g. binary flag set in IRQ).

### Validation
- No tearing visible during slide animations.
- Frame pacing measured at ~16.6ms (60 Hz) or 33ms (30 Hz) — pick target.
- FPS measurement stable.

### Risk
- 2 framebuffers × 1.5 MB = 3 MB SDRAM. Verify no conflict with other SDRAM users.
- Need to be careful: LVGL partial mode draws only dirty rectangles to back-buffer, so back-buffer must contain previous frame content. Solution: copy front→back at start of each frame OR use LVGL's `LV_DISPLAY_RENDER_MODE_DIRECT` (renders whole screen). Direct mode means LVGL renders the entire dirty region directly into back fb — and back-buffer must already match front. Either:
  - (a) Each VSYNC, schedule a DMA2D copy front→back, then LVGL adds its dirty rects on top, OR
  - (b) Track all dirty rectangles across both buffers (LVGL has `LV_DISPLAY_RENDER_MODE_FULL` style helpers).
  - Decision at implementation time based on what LVGL v9 cleanly supports.

---

## Phase 3 — Triple-Buffer Animation Compositor

**Goal:** Animations run with **zero LVGL rendering** — pure DMA2D blits between pre-rendered screens.

### Concept
- 3 SDRAM framebuffers:
  - **FB_OLD**: outgoing screen, rendered once
  - **FB_NEW**: incoming screen, rendered once
  - **FB_DISP**: shown by LTDC, composed each frame from FB_OLD + FB_NEW via DMA2D
- During animation:
  - Compute rectangle of OLD visible + rectangle of NEW visible (based on animation progress)
  - Issue 1-2 non-blocking DMA2D blits to FB_DISP
  - Add static navbar / context-bar from a constant source (or pre-baked in FB_DISP)
  - On VSYNC swap to FB_DISP

### Changes
- **New file:** `f469-disco/usermods/udisplay_f469/anim_compositor.c` + `.h`
  - C-level animation engine: `anim_start(direction, duration_ms)`, `anim_tick(progress)`.
  - Computes source/dest rectangles based on animation type + progress.
  - Issues DMA2D M2M copies between framebuffers.
- **File:** `display.c`
  - Expose `display.anim_prepare()` (render current → FB_OLD, target → FB_NEW), `display.anim_start(direction, ms)`, `display.anim_in_progress()`.
- **File:** `scenarios/MockUI/src/MockUI/basic/utils/animations.py`
  - Replace LVGL `lv.anim_t` slide implementations with calls to the new C animator when on hardware.
  - Fallback to LVGL animations on unix simulator.

### Validation
- Slide animations completely smooth at 60 FPS.
- LVGL CPU usage during animation ≈ 0.
- After animation: front-buffer = FB_NEW, becomes the new working buffer.

### Risk
- Animation API changes are invasive in Python layer — careful migration needed.
- Pre-rendering FB_NEW must complete before animation starts. With Phase 1 in place, a full screen render is ~10-15ms — acceptable as a one-time pre-animation cost.
- Memory: 3 × 1.5 MB = 4.5 MB SDRAM (we have ~14 MB free) ✅

---

## Workflow Per Phase

1. Implement changes
2. Build: `cd f469-disco && nix develop --command bash -c "make mockui ADD_LANG=de"` (or equivalent)
3. Flash: `disco flash program bin/mockui.bin --addr 0x08000000`
4. **Stop and let user verify on device.**
5. After user confirms, proceed to next phase.

---

## Skipped / Deferred

- **Phase 3 alt** (LTDC dual-layer hardware slide): potentially even faster than Phase 3, but Phase 3's DMA2D approach is sufficient and more general. Re-evaluate only if Phase 3 underperforms.
- **SRAM ping-pong (Phase 1.c)**: not beneficial — render time >> DMA2D time, nothing to overlap.
- **Direct SDRAM rendering (Phase 1.a)**: SRAM staging stays faster due to LTDC bus contention.
