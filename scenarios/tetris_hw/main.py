# main.py -- Tetris entry point for STM32F469 Discovery
import pyb
pyb.usb_mode("VCP")  # USB REPL for debugging

import tetris
tetris.main()
