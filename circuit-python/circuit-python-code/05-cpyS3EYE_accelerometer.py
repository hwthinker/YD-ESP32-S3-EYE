"""
05-cpyS3EYE_accelerometer.py
Membaca akselerometer 3-axis QMA7981/QMA6100P via I2C di CircuitPython

Board  : YD-ESP32-S3-EYE
I2C    : SDA=GPIO4, SCL=GPIO5, Addr=0x12
"""

import time
import board
import busio
import microcontroller

# I2C pins
SDA_PIN = getattr(board, "IO4", getattr(board, "D4", microcontroller.pin.GPIO4))
SCL_PIN = getattr(board, "IO5", getattr(board, "D5", microcontroller.pin.GPIO5))

QMA_ADDR = 0x12

# Registers
REG_CHIP_ID  = 0x00
REG_DX_L     = 0x01
REG_RANGE    = 0x0F
REG_BW_ODR   = 0x10
REG_PM       = 0x11
REG_SOFT_RST = 0x36

# Scale ±8g, 14-bit signed
SCALE_G = 8.0 / 8192.0

print("Inisialisasi I2C...")
i2c = busio.I2C(SCL_PIN, SDA_PIN)

def write_reg(reg, val):
    while not i2c.try_lock():
        pass
    try:
        i2c.writeto(QMA_ADDR, bytes([reg, val]))
    finally:
        i2c.unlock()

def read_reg(reg):
    while not i2c.try_lock():
        pass
    try:
        result = bytearray(1)
        # writeto_then_readfrom performs a repeated start, equivalent to endTransmission(false)
        i2c.writeto_then_readfrom(QMA_ADDR, bytes([reg]), result)
        return result[0]
    finally:
        i2c.unlock()

def read_xyz():
    while not i2c.try_lock():
        pass
    try:
        data = bytearray(6)
        i2c.writeto_then_readfrom(QMA_ADDR, bytes([REG_DX_L]), data)
    finally:
        i2c.unlock()
    
    def to14(lsb, msb):
        v = (msb << 6) | (lsb >> 2)
        # Convert to signed 14-bit
        if v & 0x2000:
            v -= 16384 # 2^14
        return v
        
    ax = to14(data[0], data[1]) * SCALE_G
    ay = to14(data[2], data[3]) * SCALE_G
    az = to14(data[4], data[5]) * SCALE_G
    return ax, ay, az

def setup():
    print("\n=== QMA Accelerometer ===")
    
    # Soft reset
    write_reg(REG_SOFT_RST, 0xB6)
    time.sleep(0.05)
    write_reg(REG_SOFT_RST, 0x00)
    time.sleep(0.01)
    
    chip_id = read_reg(REG_CHIP_ID)
    print(f"Chip ID : 0x{chip_id:02X}", end="")
    if chip_id == 0xE8: 
        print(" (QMA7981)")
    elif chip_id == 0xE7: 
        print(" (QMA6100P)")
    else: 
        print(" (unknown)")
    
    # Standby
    pm = read_reg(REG_PM) & ~0x03
    write_reg(REG_PM, pm)
    time.sleep(0.005)
    
    # Range dan BW
    write_reg(REG_RANGE, 0x04) # +/- 8g
    write_reg(REG_BW_ODR, 0x05) # 128Hz
    time.sleep(0.005)
    
    # Active mode
    write_reg(REG_PM, 0x80)
    time.sleep(0.03)
    
    print("Status  : OK, membaca data...\n")
    print("    X (g)         Y (g)         Z (g)")
    print("  ---------     ---------     ---------")

def loop():
    while True:
        try:
            ax, ay, az = read_xyz()
            print(f"  {ax:+8.4f}      {ay:+8.4f}      {az:+8.4f}")
        except Exception as e:
            print("ERROR: gagal baca sensor:", e)
        time.sleep(0.1)

setup()
loop()
