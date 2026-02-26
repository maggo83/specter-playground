from micropython import const
import lvgl as lv

# --- Menu / button sizes (1.5× scaled for 800×480 touch target) ---
BTN_HEIGHT = const(75)           # menu button height (was 50)
BTN_WIDTH = const(100)           # Percentage of container width
# Back-navigation button: W = width, H = height passed to set_size(w, h)
BACK_BTN_HEIGHT = const(70)      # used as WIDTH in set_size(w, h) (was 50)
BACK_BTN_WIDTH = const(48)       # used as HEIGHT in set_size(w, h) (was 32)
MENU_PCT = const(100)
TITLE_ROW_HEIGHT = const(60)     # fixed height reserved for the title + back-btn row
TITLE_PADDING = const(15)        # gap between title row and button container
STATUS_BTN_HEIGHT = const(50)    # status bar button height (was 30)
STATUS_BTN_WIDTH = const(60)     # status bar button width  (was 40)
SWITCH_HEIGHT = const(82)        # toggle switch height (was 55)
SWITCH_WIDTH = const(45)         # toggle switch width  (was 30)
PAD_SIZE = const(5)

# --- Status bar / content area layout ---
STATUS_BAR_PCT = const(8)        # each bar (top + bottom), % of screen height
CONTENT_PCT = const(84)          # 100 - 2 * STATUS_BAR_PCT

# --- Icon sizes ---
BTC_ICON_WIDTH = const(36)            # layout space per icon (was 24, now 1.5×)
BTC_ICON_ZOOM = const(384)            # LVGL zoom: 256=100%, 384=150%, 512=200%
ONE_LETTER_SYMBOL_WIDTH = const(16)   # status bar 1-letter label (was 11)
TWO_LETTER_SYMBOL_WIDTH = const(28)   # status bar 2-letter label (was 19)
THREE_LETTER_SYMBOL_WIDTH = const(40) # status bar 3-letter label (was 27)

# --- Font sizes (FontLoaderDE, sizes 8–28 available) ---
MENU_TITLE_FONT_SIZE = const(24)  # screen/menu title font
MENU_ITEM_FONT_SIZE = const(20)   # menu item labels and status bar labels

# Modal/popup dimensions (percentage of screen)
MODAL_WIDTH_PCT = const(75)
MODAL_HEIGHT_PCT = const(75)

# UIExplainer dimensions and style
EXPLAINER_WIDTH_PCT = const(70)   # Width of explainer text box (percentage of screen)
EXPLAINER_HEIGHT_PCT = const(40)  # Height of explainer text box (percentage of screen)
EXPLAINER_OVERLAY_OPA = const(200)  # Opacity of dim overlay (0-255, ~80% = 200)

GREEN = const("#00D100")
GREEN_HEX = lv.color_hex(0x00D100)
ORANGE = const("#FF9A00")
ORANGE_HEX = lv.color_hex(0xFF9A00)
RED = const("#F10000")
RED_HEX = lv.color_hex(0xF10000)
WHITE_HEX = lv.color_hex(0xFFFFFF)
BLACK_HEX = lv.color_hex(0x000000)