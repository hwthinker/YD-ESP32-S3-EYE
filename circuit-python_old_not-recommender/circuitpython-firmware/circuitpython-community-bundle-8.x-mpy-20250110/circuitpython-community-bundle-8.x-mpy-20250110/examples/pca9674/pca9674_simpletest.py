# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Finn Scheller
#
# SPDX-License-Identifier: MIT

import board
from digitalio import Direction

from pca9674 import PCA9674

i2c = board.I2C()

pca = (PCA9674(i2c, 0x10),)

pin = pca.get_pin(1)
pin.direction = Direction.INPUT

while True:
    print(pin.value)
