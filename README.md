# YD-ESP32-S3-EYE (espressif_esp32s3_eye V.2.2)



----

## Arduino setting

![image-20260511042139739](./assets/image-20260511042139739.png)

---

## Source Code — Daftar Program

| No | Folder | Deskripsi | Platform |
|----|--------|-----------|----------|
| 01 | [01-test-sdcard](source-code/01-test-sdcard/) | Test baca/tulis microSD Card via SDMMC | Arduino |
| 02 | [02-test-led-button](source-code/02-test-led-button/) | Test LED onboard + tombol UP/DOWN/PLAY/MENU/BOOT | Arduino |
| 03 | [03-test-mic](source-code/03-test-mic/) | Monitoring mikrofon I2S — bar graph di Serial Monitor | Arduino |
| 04 | [04-mic-stream](source-code/04-mic-stream/) | Stream audio ke Python — waveform + FFT realtime | Arduino + Python |
| 05 | [05-mic-record](source-code/05-mic-record/) | Rekam audio ke WAV + playback lewat GUI Python | Arduino + Python |
| 06 | [06-camera-stream](source-code/06-camera-stream/) | Live stream kamera ke browser via WiFi AP — auto-detect sensor | Arduino |
| 07 | [07-lcd-display](source-code/07-lcd-display/) | Demo slideshow LCD 1.3" ST7789V — warna, bentuk, animasi | Arduino |
| 08 | [08-lcd-hello](source-code/08-lcd-hello/) | Test minimal LCD ST7789V — tampilkan "Halo Apa Kabar" | Arduino |

> Setiap folder memiliki `README.md` dengan penjelasan pin, cara upload, dan cara pakai.

---

## Catatan Hardware Penting

### LCD ST7789V — Backlight (GPIO 48)

⚠️ **Backlight menggunakan P-channel MOSFET (Q2 = AO3401A), bukan N-channel.**

| Kode | Efek |
|------|------|
| `digitalWrite(48, LOW)` | Backlight **NYALA** ✓ |
| `digitalWrite(48, HIGH)` | Backlight **MATI** ✗ |

Intuisi N-channel (HIGH = ON) **tidak berlaku** di sini. Lihat [07-lcd-display/README.md](source-code/07-lcd-display/README.md) untuk penjelasan lengkap.

### LCD ST7789V — Cold Power-On (USB baru di-colokin)

Pada cold power-on, GPIO44 (LCD CS, active-LOW) mulai dari 0V → LCD ter-select sebelum firmware jalan → SPI state machine corrupt → layar hitam permanen. Fix wajib di `setup()`:

```cpp
#include <esp_system.h>
if (esp_reset_reason() == ESP_RST_POWERON) { delay(200); ESP.restart(); }
```

---

## Working firmware:

-  [esp32-s3-eye-v2.2-firmware-v0.2.0-en.bin](manufaktur-firmware\esp32-s3-eye-v2.2-firmware-v0.2.0-en.bin) 

## Step 1: Install esptool (kalau belum)

```powershell
pip install esptool
```

------

## Step 2: Erase Flash (Full Chip Erase)

Colok USB, tekan **BOOT** + **RST** (lepas RST dulu, baru lepas BOOT). Board masuk **Download Mode**.

Buka PowerShell/CMD, jalankan:

```powershell
esptool.py --chip esp32s3 --port COM5 erase-flash
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

## Step 3: Download Firmware Binary

Firmware link-mu: http://vcc-gnd.cn/vcc_gnd/esp-who/src/branch/master/default_bin/esp32-s3-eye/v2.2/esp32-s3-eye-v2.2-firmware-v0.2.0-en.bin

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

------

## Referensi

1. skematik

- https://github.com/prusa3d/Prusa-Firmware-ESP32-Cam/blob/master/doc/ESP32-S3-EYE-22/SCH_ESP32-S3-EYE-MB_20211201_V2.2.pdf
- http://vcc-gnd.cn/vcc_gnd/esp-who/src/commit/b454739d3ea4221ca96e17f88293faf625da4ff5/docs/en/get-started/ESP32-S3-EYE_Getting_Started_Guide.md
- 
