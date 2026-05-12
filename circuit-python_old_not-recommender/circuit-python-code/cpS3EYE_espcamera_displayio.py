"""
Exercise of espcamera run on
YD-ESP32-S3-EYE/CircuitPython 8.2.8
with:
cam:     OV2640
display: 240x240

ref:
https://docs.circuitpython.org/en/8.2.x/shared-bindings/espcamera
"""
import os, sys

import board
import busio
import espcamera

from displayio import (
    Bitmap,
    Group,
    TileGrid,
    ColorConverter,
    Colorspace,
)

display = board.DISPLAY

info = os.uname()[4] + "\n" + \
       sys.implementation[0] + " " + os.uname()[3] + "\n" + \
       "board.DISPLAY: " + str(display.width) + "x" + str(display.height)
print("=======================================")
print(info)
print("=======================================")
print()

i2c = busio.I2C(scl=board.SCL, sda=board.SDA)
cam = espcamera.Camera(
    data_pins=board.CAMERA_DATA,
    external_clock_pin=board.CAMERA_XCLK,
    pixel_clock_pin=board.CAMERA_PCLK,
    vsync_pin=board.CAMERA_VSYNC,
    href_pin=board.CAMERA_HREF,
    pixel_format=espcamera.PixelFormat.RGB565,
    frame_size=espcamera.FrameSize.R240X240,
    i2c=i2c,
    framebuffer_count=2)

bitmap = Bitmap(cam.width, cam.height, 65536)
if bitmap is None:
    raise SystemExit("Could not allocate a bitmap")

#cam.colorbar = True
#cam.special_effect = 0
#0 - No Effect
#1 - Negative
#2 - Grayscale
#3 - Red Tint
#4 - Green Tint
#5 - Blue Tint
#6 - Sepia
cam.vflip = True

print()
print("pixel_format:\t", cam.pixel_format)
print("frame_size:\t", cam.frame_size)
print("contrast:\t", cam.contrast)
print("brightness:\t", cam.brightness)
print("saturation:\t", cam.saturation)
print("sharpness:\t", cam.sharpness)
print("denoise:\t", cam.denoise)
print("gain_ceiling:\t", cam.gain_ceiling)
print("quality:\t", cam.quality)
print("whitebal:\t", cam.whitebal)
print("gain_ctrl:\t", cam.gain_ctrl)
print("exposure_ctrl:\t", cam.exposure_ctrl)
print("hmirror:\t", cam.hmirror)
print("vflip:\t\t", cam.vflip)
print("aec2:\t\t", cam.aec2)
print("awb_gain:\t", cam.awb_gain)
print("agc_gain:\t", cam.agc_gain)
print("aec_value:\t", cam.aec_value)
print("special_effect:\t", cam.special_effect)
print("wb_mode:\t", cam.wb_mode)
print("ae_level:\t", cam.ae_level)
print("dcw:\t\t", cam.dcw)
print("bpc:\t\t", cam.bpc)
print("wpc:\t\t", cam.wpc)
print("raw_gma:\t", cam.raw_gma)
print("lenc:\t\t", cam.lenc)
print("max_frame_size:\t", cam.max_frame_size)
print("address:\t", hex(cam.address))
print("sensor_name:\t", cam.sensor_name)
print("supports_jpeg:\t", cam.supports_jpeg)
print("height:\t\t", cam.height);
print("width:\t\t", cam.width)
print("grab_mode:\t", cam.grab_mode)
print("framebuffer_count:\t", cam.framebuffer_count)

g = Group(scale=1, x=(display.width - cam.width) // 2, y=(display.height - cam.height) // 2)

#colorspace = Colorspace.BGR555
#colorspace = Colorspace.BGR555_SWAPPED
#colorspace = Colorspace.RGB565
#colorspace = Colorspace.BGR565_SWAPPED
#colorspace = Colorspace.L8
#colorspace = Colorspace.RGB555
#colorspace = Colorspace.RGB555_SWAPPED
#colorspace = Colorspace.RGB565
colorspace = Colorspace.RGB565_SWAPPED
#colorspace = Colorspace.RGB888

tg = TileGrid(
    bitmap,
    pixel_shader=ColorConverter(input_colorspace=colorspace)
)

g.append(tg)
display.show(g)

display.auto_refresh = True
while True:
    if cam.frame_available:
        tg.bitmap = cam.take()

