# -----------------------------------------------------------------------------
# Testprogramm for the MHZ19 library for CircuitPython.
#
# Website: https://github.com/bablokb/circuitpython-mhz19
#
# -----------------------------------------------------------------------------

import board
import busio
import time
from mhz19 import MHZ19

# pins - works for boards with defined RX/TX or RP2040
# change as required
PINS_TX = getattr(board,"TX",board.GP0)
PINS_RX = getattr(board,"RX",board.GP1)

INTERVAL = 10
RETRIES  = 3

uart = busio.UART(PIN_TX, PIN_RX, baudrate=9600)
mhz19 = MHZ19(uart)

print('C/MHZ ppm,T/MHZ °C,status')

while True:
  data = [0,0,-1]
  while i in range(RETRIES):
    try:
      data = mhz19.read()
      break
    except:
      pass
  print(f",{data[0]},{data[1]:.1f},{data[2]}")
  time.sleep(INTERVAL)
