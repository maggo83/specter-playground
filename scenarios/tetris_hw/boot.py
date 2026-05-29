# boot.py -- hardware init for tetris scenario
import pyb

# Power on the display
pwr = pyb.Pin("B15", pyb.Pin.OUT)
pwr.on()

# Import platform to trigger early SDRAM init
import platform
