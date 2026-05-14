"""
06-cpyS3EYE_imu_cube.py
3D Wireframe Cube - tilt the board, the cube stays level in world-space
Implementasi CircuitPython dari 10-imu-cube.ino
Board: YD-ESP32-S3-EYE
"""

import board
import displayio
import busio
import microcontroller
import time
import math
import bitmaptools

# --- Display Setup ---
display = board.DISPLAY
display.auto_refresh = False

bitmap = displayio.Bitmap(display.width, display.height, 2)
palette = displayio.Palette(2)
palette[0] = 0x000000  # Black background
palette[1] = 0x00FFFF  # Cyan wireframe

tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
group = displayio.Group()
group.append(tile_grid)
display.root_group = group

# --- IMU QMA7981 / QMA6100P Setup ---
SDA_PIN = getattr(board, "IO4", getattr(board, "D4", microcontroller.pin.GPIO4))
SCL_PIN = getattr(board, "IO5", getattr(board, "D5", microcontroller.pin.GPIO5))
QMA_ADDR = 0x12
REG_DX_L = 0x01
SCALE_G = 8.0 / 8192.0

i2c = busio.I2C(SCL_PIN, SDA_PIN)

def write_reg(reg, val):
    while not i2c.try_lock(): pass
    try: i2c.writeto(QMA_ADDR, bytes([reg, val]))
    finally: i2c.unlock()

def read_reg(reg):
    while not i2c.try_lock(): pass
    try:
        res = bytearray(1)
        i2c.writeto_then_readfrom(QMA_ADDR, bytes([reg]), res)
        return res[0]
    finally: i2c.unlock()

def init_imu():
    write_reg(0x36, 0xB6)  # Soft reset
    time.sleep(0.05)
    write_reg(0x36, 0x00)
    time.sleep(0.01)
    
    pm = read_reg(0x11) & ~0x03
    write_reg(0x11, pm)
    write_reg(0x0F, 0x04)  # +/- 8g
    write_reg(0x10, 0x05)  # 128 Hz
    write_reg(0x11, 0x80)  # Active mode
    time.sleep(0.03)

def read_xyz():
    while not i2c.try_lock(): pass
    try:
        data = bytearray(6)
        i2c.writeto_then_readfrom(QMA_ADDR, bytes([REG_DX_L]), data)
    finally: i2c.unlock()
    
    def to14(lsb, msb):
        v = (msb << 6) | (lsb >> 2)
        if v & 0x2000: v -= 16384
        return v
    return to14(data[0], data[1]) * SCALE_G, to14(data[2], data[3]) * SCALE_G, to14(data[4], data[5]) * SCALE_G

init_imu()

# --- Cube Geometry & Parameters ---
verts = [
    [-1, -1, -1], [ 1, -1, -1], [ 1,  1, -1], [-1,  1, -1],
    [-1, -1,  1], [ 1, -1,  1], [ 1,  1,  1], [-1,  1,  1]
]

edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7)
]

CUBE_SIZE = 280.0
PERSP_DIST = 4.5
SCREEN_CX = display.width // 2
SCREEN_CY = display.height // 2
SENSITIVITY = 1.4
SMOOTH = 0.08

sax = 0.0
say = 0.0
saz = -1.0

# --- Main Loop ---
while True:
    try:
        ax, ay, az = read_xyz()
    except Exception:
        continue
    
    # Low-pass filter
    sax = sax * (1.0 - SMOOTH) + ax * SMOOTH
    say = say * (1.0 - SMOOTH) + ay * SMOOTH
    saz = saz * (1.0 - SMOOTH) + az * SMOOTH
    
    # Normalize
    mag = math.sqrt(sax*sax + say*say + saz*saz)
    if mag < 0.01: mag = 1.0
    nax = sax / mag
    nay = say / mag
    naz = saz / mag
    
    # Calculate angles
    angleX = -nay * SENSITIVITY
    angleY = -nax * SENSITIVITY
    
    cosX = math.cos(angleX)
    sinX = math.sin(angleX)
    cosY = math.cos(angleY)
    sinY = math.sin(angleY)
    
    px = [0]*8
    py = [0]*8
    
    # 3D to 2D Projection
    for i in range(8):
        x, y, z = verts[i]
        
        # Rotate Y (pitch)
        x1 = x * cosY + z * sinY
        z1 = -x * sinY + z * cosY
        y1 = y
        
        # Rotate X (roll)
        y2 = y1 * cosX - z1 * sinX
        z2 = y1 * sinX + z1 * cosX
        x2 = x1
        
        # Perspective
        s = CUBE_SIZE / (z2 + PERSP_DIST)
        px[i] = int(SCREEN_CX + x2 * s)
        py[i] = int(SCREEN_CY + y2 * s)
    
    # Clear screen
    bitmap.fill(0)
    
    # Draw wireframe
    for a, b in edges:
        bitmaptools.draw_line(bitmap, px[a], py[a], px[b], py[b], 1)
        
    display.refresh()
    time.sleep(0.01)
