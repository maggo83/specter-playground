"""
tetris.py — Tetris for MicroPython + LVGL 9.x
Screen: 480 x 800 (portrait)

Layout
------
+------------------+------+
|                  |      |  ^
|   GAME AREA      | INFO |  | 720 px
|   360x720 px     | 120px|  |
|   (10x20 cells,  |      |  |
|    cell = 36 px) |      |  v
+------------------+------+
|     INPUT BAR  480x80   |
+-------------------------+

Cheat code: edit CHEAT_SEQUENCE (list of 'left'/'right'/'down'/'rotate').
"""

import display
import lvgl as lv
import utime as time
import urandom as _urandom

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------
CHEAT_SEQUENCE     = ["rotate", "down", "rotate", "down", "rotate", "down"]
CHEAT_HISTORY_LEN  = max(len(CHEAT_SEQUENCE), 10)

SCREEN_W = 480
SCREEN_H = 800

COLS   = 10
ROWS   = 20
CELL   = 36        # px — square cells

GRID_W  = COLS * CELL   # 360
GRID_H  = ROWS * CELL   # 720
INPUT_H = 80
INFO_W  = SCREEN_W - GRID_W   # 120

LONG_PRESS_MS      = 400   # ms before continuous mode kicks in
LONG_PRESS_RATE_MS = 80    # ms between steps in continuous mode

# Gravity in ms per drop step; index = score // 10 (capped)
GRAVITY_LEVELS = [800, 720, 640, 560, 480, 400, 340, 280, 220, 160, 120, 100, 80]

# ---------------------------------------------------------------------------
# Piece definitions  (row, col) offsets from spawn origin, 4 rotations
# ---------------------------------------------------------------------------
PIECES = {
    "I": [
        [(0,0),(0,1),(0,2),(0,3)],
        [(0,2),(1,2),(2,2),(3,2)],
        [(1,0),(1,1),(1,2),(1,3)],
        [(0,1),(1,1),(2,1),(3,1)],
    ],
    "O": [
        [(0,0),(0,1),(1,0),(1,1)],
        [(0,0),(0,1),(1,0),(1,1)],
        [(0,0),(0,1),(1,0),(1,1)],
        [(0,0),(0,1),(1,0),(1,1)],
    ],
    "T": [
        [(0,1),(1,0),(1,1),(1,2)],
        [(0,1),(1,1),(1,2),(2,1)],
        [(1,0),(1,1),(1,2),(2,1)],
        [(0,1),(1,0),(1,1),(2,1)],
    ],
    "S": [
        [(0,1),(0,2),(1,0),(1,1)],
        [(0,1),(1,1),(1,2),(2,2)],
        [(1,1),(1,2),(2,0),(2,1)],
        [(0,0),(1,0),(1,1),(2,1)],
    ],
    "Z": [
        [(0,0),(0,1),(1,1),(1,2)],
        [(0,2),(1,1),(1,2),(2,1)],
        [(1,0),(1,1),(2,1),(2,2)],
        [(0,1),(1,0),(1,1),(2,0)],
    ],
    "J": [
        [(0,0),(1,0),(1,1),(1,2)],
        [(0,1),(0,2),(1,1),(2,1)],
        [(1,0),(1,1),(1,2),(2,2)],
        [(0,1),(1,1),(2,0),(2,1)],
    ],
    "L": [
        [(0,2),(1,0),(1,1),(1,2)],
        [(0,1),(1,1),(2,1),(2,2)],
        [(1,0),(1,1),(1,2),(2,0)],
        [(0,0),(0,1),(1,1),(2,1)],
    ],
}

PIECE_COLORS = {
    "I": lv.color_make(0,   220, 220),
    "O": lv.color_make(220, 220,   0),
    "T": lv.color_make(170,   0, 220),
    "S": lv.color_make(0,   200,   0),
    "Z": lv.color_make(220,   0,   0),
    "J": lv.color_make(0,    80, 220),
    "L": lv.color_make(220, 130,   0),
}
PIECE_NAMES  = list(PIECES.keys())
EMPTY_COLOR  = lv.color_make(30,  30,  30)
BORDER_COLOR = lv.color_make(60,  60,  60)
WHITE_COLOR  = lv.color_make(255, 255, 255)


def _rand_piece():
    return PIECE_NAMES[_urandom.getrandbits(8) % len(PIECE_NAMES)]


# ---------------------------------------------------------------------------
# Helper: build a plain container with no scroll, no padding, no border
# ---------------------------------------------------------------------------
def _plain_obj(parent, w, h, x, y, bg=None):
    o = lv.obj(parent)
    o.set_size(w, h)
    o.set_pos(x, y)
    o.set_style_pad_all(0, 0)
    o.set_style_border_width(0, 0)
    o.set_style_radius(0, 0)
    o.set_scroll_dir(lv.DIR.NONE)
    if bg is not None:
        o.set_style_bg_color(bg, 0)
        o.set_style_bg_opa(lv.OPA.COVER, 0)
    return o


# ---------------------------------------------------------------------------
# TetrisGame — the root widget
# ---------------------------------------------------------------------------
class TetrisGame(lv.obj):

    # ------------------------------------------------------------------ init
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_size(SCREEN_W, SCREEN_H)
        self.set_pos(0, 0)
        self.set_style_bg_color(lv.color_make(0, 0, 0), 0)
        self.set_style_bg_opa(lv.OPA.COVER, 0)
        self.set_style_pad_all(0, 0)
        self.set_style_border_width(0, 0)
        self.set_scroll_dir(lv.DIR.NONE)

        # ---- game area
        self._game_area = _plain_obj(self, GRID_W, GRID_H, 0, 0,
                                     bg=lv.color_make(0, 0, 0))

        # board cells — 10×20 lv.obj squares
        self._cells = []
        for r in range(ROWS):
            row_cells = []
            for c in range(COLS):
                cell = lv.obj(self._game_area)
                cell.set_size(CELL - 1, CELL - 1)
                cell.set_pos(c * CELL, r * CELL)
                cell.set_style_bg_color(EMPTY_COLOR, 0)
                cell.set_style_bg_opa(lv.OPA.COVER, 0)
                cell.set_style_border_color(BORDER_COLOR, 0)
                cell.set_style_border_width(1, 0)
                cell.set_style_radius(0, 0)
                cell.set_style_pad_all(0, 0)
                cell.set_scroll_dir(lv.DIR.NONE)
                row_cells.append(cell)
            self._cells.append(row_cells)

        # ---- info panel
        info = _plain_obj(self, INFO_W, GRID_H, GRID_W, 0,
                          bg=lv.color_make(20, 20, 20))

        next_lbl = lv.label(info)
        next_lbl.set_text("NEXT")
        next_lbl.set_style_text_color(lv.color_make(200, 200, 200), 0)
        next_lbl.set_style_text_font(lv.font_montserrat_22, 0)
        next_lbl.set_pos(4, 4)

        # next-piece preview: 4×4 cells
        PREVIEW_Y = 28
        self._np_cells = []
        for r in range(4):
            row = []
            for c in range(4):
                cell = lv.obj(info)
                cell.set_size(CELL - 1, CELL - 1)
                cell.set_pos(c * CELL, PREVIEW_Y + r * CELL)
                cell.set_style_bg_color(EMPTY_COLOR, 0)
                cell.set_style_bg_opa(lv.OPA.COVER, 0)
                cell.set_style_border_width(0, 0)
                cell.set_style_radius(0, 0)
                cell.set_style_pad_all(0, 0)
                cell.set_scroll_dir(lv.DIR.NONE)
                row.append(cell)
            self._np_cells.append(row)

        self._score_lbl = lv.label(info)
        self._score_lbl.set_text("Lines\n0")
        self._score_lbl.set_style_text_color(lv.color_make(200, 200, 200), 0)
        self._score_lbl.set_style_text_font(lv.font_montserrat_22, 0)
        self._score_lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self._score_lbl.set_width(INFO_W - 8)
        self._score_lbl.set_pos(0, PREVIEW_Y + 4 * CELL + 10)

        # ---- input bar
        ibar = _plain_obj(self, SCREEN_W, INPUT_H, 0, GRID_H,
                          bg=lv.color_make(40, 40, 40))

        BTN_W = SCREEN_W // 4
        btn_defs = [
            (lv.SYMBOL.LEFT,    "left"),
            (lv.SYMBOL.DOWN,    "down"),
            (lv.SYMBOL.LOOP,    "rotate"),
            (lv.SYMBOL.RIGHT,   "right"),
        ]
        self._held_action   = None
        self._hold_start_ms = 0
        self._hold_last_ms  = 0

        for i, (sym, action) in enumerate(btn_defs):
            btn = lv.button(ibar)
            btn.set_size(BTN_W, INPUT_H)
            btn.set_pos(i * BTN_W, 0)
            btn.set_style_bg_color(lv.color_make(60, 60, 60), 0)
            btn.set_style_bg_color(lv.color_make(100, 100, 100), lv.STATE.PRESSED)
            btn.set_style_border_width(0, 0)
            btn.set_style_radius(0, 0)
            lbl = lv.label(btn)
            lbl.set_text(sym)
            lbl.set_style_text_font(lv.font_montserrat_28, 0)
            lbl.set_style_text_color(lv.color_make(220, 220, 220), 0)
            lbl.center()
            # Use factory functions to capture `action` by value in closures
            btn.add_event_cb(self._make_press_cb(action),   lv.EVENT.PRESSED,    None)
            btn.add_event_cb(self._release_cb,              lv.EVENT.RELEASED,   None)
            btn.add_event_cb(self._release_cb,              lv.EVENT.PRESS_LOST, None)

        # Gravity timer — paused until game starts
        self._gravity_timer = lv.timer_create(self._gravity_tick, GRAVITY_LEVELS[0], None)
        self._gravity_timer.pause()

        # Hold-repeat timer — fires every 30 ms, checks elapsed time itself
        self._hold_timer = lv.timer_create(self._hold_tick, 30, None)
        self._hold_timer.pause()

        # Flicker timer — paused until a line clears
        self._flicker_timer = lv.timer_create(self._flicker_tick, 120, None)
        self._flicker_timer.pause()

        self._overlay = None
        self._state   = "init"
        self._show_init_screen()

    # ------------------------------------------------------------------ closure factories

    def _make_press_cb(self, action):
        """Return a closure that calls _on_action_press(action)."""
        def cb(e):
            self._on_action_press(action)
        return cb

    def _release_cb(self, e):
        self._held_action = None

    # ------------------------------------------------------------------ overlays

    def _make_overlay(self, opa=200):
        ov = _plain_obj(self, SCREEN_W, SCREEN_H, 0, 0,
                        bg=lv.color_make(0, 0, 0))
        ov.set_style_bg_opa(opa, 0)
        return ov

    def _destroy_overlay(self):
        if self._overlay is not None:
            self._overlay.delete()
            self._overlay = None

    def _show_init_screen(self):
        self._destroy_overlay()
        ov = self._make_overlay(230)

        title = lv.label(ov)
        title.set_text("TETRIS")
        title.set_style_text_font(lv.font_montserrat_28, 0)
        title.set_style_text_color(lv.color_make(0, 220, 220), 0)
        title.align(lv.ALIGN.CENTER, 0, -80)

        btn = lv.button(ov)
        btn.set_size(180, 60)
        btn.align(lv.ALIGN.CENTER, 0, 20)
        btn.set_style_bg_color(lv.color_make(0, 160, 160), 0)
        btn.set_style_radius(10, 0)
        btn.set_style_border_width(0, 0)
        lbl = lv.label(btn)
        lbl.set_text("Ready")
        lbl.set_style_text_font(lv.font_montserrat_28, 0)
        lbl.center()
        btn.add_event_cb(self._on_ready, lv.EVENT.CLICKED, None)

        self._overlay = ov

    def _show_game_over(self):
        self._destroy_overlay()
        ov = self._make_overlay(180)

        lbl = lv.label(ov)
        lbl.set_text("GAME OVER")
        lbl.set_style_text_font(lv.font_montserrat_28, 0)
        lbl.set_style_text_color(lv.color_make(220, 50, 50), 0)
        lbl.align(lv.ALIGN.CENTER, 0, -60)

        btn = lv.button(ov)
        btn.set_size(180, 60)
        btn.align(lv.ALIGN.CENTER, 0, 20)
        btn.set_style_bg_color(lv.color_make(160, 60, 60), 0)
        btn.set_style_radius(10, 0)
        btn.set_style_border_width(0, 0)
        lbl2 = lv.label(btn)
        lbl2.set_text("Again")
        lbl2.set_style_text_font(lv.font_montserrat_28, 0)
        lbl2.center()
        btn.add_event_cb(self._on_again, lv.EVENT.CLICKED, None)

        self._overlay = ov

    def _show_you_won(self):
        self._destroy_overlay()
        self._gravity_timer.pause()
        self._hold_timer.pause()
        self._flicker_timer.pause()

        ov = self._make_overlay(200)

        lbl = lv.label(ov)
        lbl.set_text("YOU WON!")
        lbl.set_style_text_font(lv.font_montserrat_28, 0)
        lbl.set_style_text_color(lv.color_make(255, 215, 0), 0)
        lbl.align(lv.ALIGN.CENTER, 0, -60)

        sub = lv.label(ov)
        sub.set_text("Cheat code activated")
        sub.set_style_text_font(lv.font_montserrat_22, 0)
        sub.set_style_text_color(lv.color_make(200, 200, 200), 0)
        sub.align(lv.ALIGN.CENTER, 0, 10)

        self._overlay = ov

    # ------------------------------------------------------------------ game start

    def _start_game(self):
        self._board           = [[None] * COLS for _ in range(ROWS)]
        self._score           = 0
        self._input_history   = []
        self._flicker_rows    = []
        self._flicker_state   = False
        self._flicker_count   = 0
        self._waiting_flicker = False

        self._next_piece_name = _rand_piece()
        self._spawn_piece()
        self._update_score_label()
        self._draw_board()
        self._draw_next_piece()

        level = 0
        self._gravity_timer.set_period(GRAVITY_LEVELS[level])
        self._gravity_timer.resume()
        self._hold_timer.resume()
        self._state = "running"

    def _spawn_piece(self):
        name = self._next_piece_name
        self._piece_name  = name
        self._piece_rot   = 0
        self._piece_row   = 0
        self._piece_col   = COLS // 2 - 2
        self._piece_color = PIECE_COLORS[name]
        self._next_piece_name = _rand_piece()
        self._draw_next_piece()
        if not self._piece_fits(self._piece_row, self._piece_col, self._piece_rot):
            self._game_over()

    # ------------------------------------------------------------------ movement helpers

    def _piece_cells(self, row, col, rot):
        return [(row + dr, col + dc) for dr, dc in PIECES[self._piece_name][rot]]

    def _piece_fits(self, row, col, rot):
        for r, c in self._piece_cells(row, col, rot):
            if r < 0 or r >= ROWS or c < 0 or c >= COLS:
                return False
            if self._board[r][c] is not None:
                return False
        return True

    # ------------------------------------------------------------------ moves

    def _move_left(self):
        nc = self._piece_col - 1
        if self._piece_fits(self._piece_row, nc, self._piece_rot):
            self._piece_col = nc
            self._draw_board()

    def _move_right(self):
        nc = self._piece_col + 1
        if self._piece_fits(self._piece_row, nc, self._piece_rot):
            self._piece_col = nc
            self._draw_board()

    def _move_down(self):
        """Returns True if moved, False if locked."""
        nr = self._piece_row + 1
        if self._piece_fits(nr, self._piece_col, self._piece_rot):
            self._piece_row = nr
            self._draw_board()
            return True
        self._lock_piece()
        return False

    def _rotate(self):
        nr = (self._piece_rot + 1) % 4
        for dc in (0, -1, 1, -2, 2):
            if self._piece_fits(self._piece_row, self._piece_col + dc, nr):
                self._piece_col += dc
                self._piece_rot  = nr
                self._draw_board()
                return

    def _lock_piece(self):
        for r, c in self._piece_cells(self._piece_row, self._piece_col, self._piece_rot):
            self._board[r][c] = self._piece_color
        self._check_lines()

    def _check_lines(self):
        full = [r for r in range(ROWS)
                if all(self._board[r][c] is not None for c in range(COLS))]
        if full:
            self._flicker_rows    = full
            self._flicker_count   = 6        # 3 on/off pairs
            self._flicker_state   = True
            self._waiting_flicker = True
            self._draw_board()
            self._flicker_timer.resume()
        else:
            self._spawn_piece()

    def _flicker_tick(self, t):
        if self._flicker_count <= 0:
            self._flicker_timer.pause()
            self._clear_lines(self._flicker_rows)
            self._flicker_rows    = []
            self._waiting_flicker = False
            self._spawn_piece()
            self._draw_board()   # refresh: show cleared board + new piece
            return
        self._flicker_state  = not self._flicker_state
        self._flicker_count -= 1
        self._draw_board()

    def _clear_lines(self, rows):
        for r in sorted(rows, reverse=True):
            del self._board[r]
            self._board.insert(0, [None] * COLS)
        self._score += len(rows)
        self._update_score_label()
        level = min(self._score // 10, len(GRAVITY_LEVELS) - 1)
        self._gravity_timer.set_period(GRAVITY_LEVELS[level])

    def _game_over(self):
        self._state = "gameover"
        self._gravity_timer.pause()
        self._hold_timer.pause()
        self._flicker_timer.pause()
        self._draw_board()
        self._show_game_over()

    # ------------------------------------------------------------------ rendering

    def _draw_board(self):
        # Locked board cells
        for r in range(ROWS):
            for c in range(COLS):
                color = self._board[r][c]
                self._cells[r][c].set_style_bg_color(
                    EMPTY_COLOR if color is None else color, 0)

        # During flicker: override the full rows
        if self._waiting_flicker and self._flicker_rows:
            fc = WHITE_COLOR if self._flicker_state else EMPTY_COLOR
            for r in self._flicker_rows:
                for c in range(COLS):
                    self._cells[r][c].set_style_bg_color(fc, 0)
            return   # don't draw active piece while flickering

        # Active piece
        if self._state == "running":
            for r, c in self._piece_cells(
                    self._piece_row, self._piece_col, self._piece_rot):
                if 0 <= r < ROWS and 0 <= c < COLS:
                    self._cells[r][c].set_style_bg_color(self._piece_color, 0)

    def _draw_next_piece(self):
        # Clear preview
        for r in range(4):
            for c in range(4):
                self._np_cells[r][c].set_style_bg_color(EMPTY_COLOR, 0)
        # Centre piece in 4×4 grid
        name    = self._next_piece_name
        color   = PIECE_COLORS[name]
        offsets = PIECES[name][0]
        min_c = min(dc for _, dc in offsets)
        max_c = max(dc for _, dc in offsets)
        min_r = min(dr for dr, _ in offsets)
        max_r = max(dr for dr, _ in offsets)
        off_c = (4 - (max_c - min_c + 1)) // 2 - min_c
        off_r = (4 - (max_r - min_r + 1)) // 2 - min_r
        for dr, dc in offsets:
            nr, nc = dr + off_r, dc + off_c
            if 0 <= nr < 4 and 0 <= nc < 4:
                self._np_cells[nr][nc].set_style_bg_color(color, 0)

    def _update_score_label(self):
        self._score_lbl.set_text("Lines\n%d" % self._score)

    # ------------------------------------------------------------------ timers

    def _gravity_tick(self, t):
        if self._state != "running" or self._waiting_flicker:
            return
        self._move_down()

    def _hold_tick(self, t):
        if self._held_action is None or self._state != "running":
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, self._hold_start_ms) < LONG_PRESS_MS:
            return
        if time.ticks_diff(now, self._hold_last_ms) >= LONG_PRESS_RATE_MS:
            self._hold_last_ms = now
            self._record_input(self._held_action)
            self._dispatch_action(self._held_action)

    # ------------------------------------------------------------------ input

    def _record_input(self, action):
        self._input_history.append(action)
        if len(self._input_history) > CHEAT_HISTORY_LEN:
            self._input_history.pop(0)
        n = len(CHEAT_SEQUENCE)
        if (len(self._input_history) >= n
                and self._input_history[-n:] == CHEAT_SEQUENCE):
            self._state = "won"
            self._show_you_won()

    def _on_action_press(self, action):
        if self._state != "running":
            return
        self._record_input(action)
        if self._state != "running":   # cheat may have triggered
            return
        self._dispatch_action(action)
        if action != "rotate":          # rotate does not auto-repeat on long-press
            self._held_action   = action
            self._hold_start_ms = time.ticks_ms()
            self._hold_last_ms  = self._hold_start_ms

    def _dispatch_action(self, action):
        if   action == "left":   self._move_left()
        elif action == "right":  self._move_right()
        elif action == "down":   self._move_down()
        elif action == "rotate": self._rotate()

    # ------------------------------------------------------------------ overlay callbacks

    def _on_ready(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        self._destroy_overlay()
        self._start_game()

    def _on_again(self, e):
        if e.get_code() != lv.EVENT.CLICKED:
            return
        self._destroy_overlay()
        self._start_game()


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
display.init()

scr = TetrisGame()   # no parent → proper screen-level object for lv.screen_load


def main():
    lv.theme_default_init(
        None,
        lv.palette_main(lv.PALETTE.CYAN),
        lv.palette_main(lv.PALETTE.GREY),
        True,
        lv.font_montserrat_22,
    )
    lv.screen_load(scr)
    while True:
        time.sleep_ms(16)
        display.update(16)


if __name__ == "__main__":
    main()
