# YD-ESP32-S3-EYE (espressif_esp32s3_eye V.2.2)

## Burning firmware from manufaktur

----



## Working firmware:

-  [esp32-s3-eye-v2.2-firmware-v0.2.0-en.bin](manufaktur-firmware\esp32-s3-eye-v2.2-firmware-v0.2.0-en.bin) 

## Step 1: Install esptool (kalau belum)

```powershell
pip install esptool
```

------

## Step 2: Erase lash (Full Chip Erase)

Colok USB, tekan **BOOT** + **RST** (lepas RST dulu, baru lepas BOOT). Board masuk **Download Mode**.

Buka PowerShell/CMD, jalankan:

```powershell
esptool --chip esp32s3 --port COM5 erase-flash
```

**Expected output:**

```plain
Connecting....
Chip is ESP32-S3
...
Erasing flash (this may take a while)...
Chip erase completed successfully in X.Xs
Hard resetting via RTS pin...
```

------

## Step 3: Download Firmware Binary V2.2

Firmware link-mu pastian yang versi 2.2 bukan versi yang lain: http://vcc-gnd.cn/vcc_gnd/esp-who/src/branch/master/default_bin/esp32-s3-eye/v2.2/esp32-s3-eye-v2.2-firmware-v0.2.0-en.bin

------

## Step 4: Flash Firmware

```powershell
esptool --chip esp32s3 --port COM5 --baud 921600 write-flash -z 0x0  esp32-s3-eye-v2.2-firmware-v0.2.0-en.bin 
```

| Parameter        | Arti                                                |
| :--------------- | :-------------------------------------------------- |
| `--chip esp32s3` | Target chip ESP32-S3                                |
| `--port COM5`    | Port serial board-mu                                |
| `--baud 921600`  | Kecepatan upload (bisa turun ke 460800 kalau gagal) |
| `write-flash`    | Perintah tulis flash                                |
| `-z`             | Compress data sebelum kirim                         |
| `0x0`            | Alamat awal flash (offset 0)                        |
| `nama_file.bin`  | File firmware                                       |

------

## Step 5: Reset Board

Setelah flash selesai, tekan **RST** button saja (tanpa BOOT) untuk boot normal.

------

## Kalau Gagal Connecting

Coba turunkan baud rate:

```powershell
esptool.py --chip esp32s3 --port COM5 --baud 460800 write-flash -z 0x0 esp32-s3-eye-v2.2-firmware-v0.2.0-en.bin 
```

```powershell
# List semua COM port
python -m serial.tools.list_ports

# Atau cek esptool detect
esptool.py --port COM5 chip_id
```

