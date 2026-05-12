"""
LCD/Color test on
YD-ESP32-S3-EYE/CircuitPython 8.2.8
"""
import os, sys
import board
import time
import displayio
import terminalio
from adafruit_display_text import label

display = board.DISPLAY

#=======================================
info = os.uname()[4] + "\n" + \
       sys.implementation[0] + " " + os.uname()[3] + "\n" + \
       "board.DISPLAY: " + str(display.width) + "x" + str(display.height)
print("=======================================")
print(info)
print("=======================================")
print()

# Make the display context
bgGroup = displayio.Group()
display.show(bgGroup)

bg_bitmap = displayio.Bitmap(display.width, display.height, 1)  # with one color
bg_palette = displayio.Palette(1)
bg_palette[0] = 0xFFFFFF  # White
bg_sprite = displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette, x=0, y=0)
bgGroup.append(bg_sprite)

colorSet = ((0xFF0000, "RED"),
            (0x00FF00, "GREEN"),
            (0x0000FF, "BLUE"),
            (0xFFFFFF, "WHITE"),
            (0x000000, "BLACK"))

color_bitmap = displayio.Bitmap(display.width-2, display.height-2, 1)  # with one color
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000  # BLACK
color_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=1, y=1)
bgGroup.append(color_sprite)

# Draw label
text_group = displayio.Group(scale=1, x=20, y=120)
text = "Hello\n" + os.uname()[4]
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
text_group.append(text_area)  # Subgroup for text scaling
bgGroup.append(text_group)

time.sleep(2)
text_group.scale = 2
time.sleep(2)
text_group.scale = 3

while True:
    for i in colorSet:
        time.sleep(2)
        color_palette[0] = i[0]
        text_area.text = i[1]
        text_area.color = i[0] ^ 0xFFFFFF
