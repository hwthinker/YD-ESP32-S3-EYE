# YD-ESP32-S3-EYE (espressif_esp32s3_eye V.2.2)

Proyek eksplorasi penuh YD-ESP32-S3-EYE — mencakup pengujian semua peripheral onboard (SD Card, LED, Tombol, Mikrofon I2S, Kamera OV2640, LCD ST7789V) menggunakan Arduino IDE dan CircuitPython.

----

## Arduino IDE Settings

![image-20260511042139739](./assets/image-20260511042139739.png)

| Setting              | Nilai                            |
|----------------------|----------------------------------|
| Board                | ESP32S3 Dev Module               |
| Port                 | COM5 (sesuaikan)                 |
| Upload Speed         | 921600                           |
| USB Mode             | Hardware CDC and JTAG            |
| PSRAM                | OPI PSRAM                        |
| Partition Scheme     | Huge APP (3MB No OTA/1MB SPIFFS) — untuk kamera |

---

## Source Code — Daftar Program

### Arduino (source-code-arduino/)

| No | Folder | Deskripsi | Platform |
|----|--------|-----------|----------|
| 01 | [01-test-sdcard](source-code-arduino/01-test-sdcard/) | Test baca/tulis microSD Card via SDMMC | Arduino |
| 02 | [02-test-led-button](source-code-arduino/02-test-led-button/) | Test LED onboard + tombol UP/DOWN/PLAY/MENU/BOOT | Arduino |
| 03 | [03-test-mic](source-code-arduino/03-test-mic/) | Monitoring mikrofon I2S — bar graph di Serial Monitor | Arduino |
| 04 | [04-mic-stream](source-code-arduino/04-mic-stream/) | Stream audio ke Python — waveform + FFT realtime | Arduino + Python |
| 05 | [05-mic-record](source-code-arduino/05-mic-record/) | Rekam audio ke WAV + playback lewat GUI Python | Arduino + Python |
| 06 | [06-camera-stream](source-code-arduino/06-camera-stream/) | Live stream kamera ke browser via WiFi AP — auto-detect sensor | Arduino |
| 07 | [07-lcd-display](source-code-arduino/07-lcd-display/) | Demo slideshow LCD 1.3" ST7789V — warna, bentuk, animasi | Arduino |
| 08 | [08-lcd-hello](source-code-arduino/08-lcd-hello/) | Test minimal LCD ST7789V — tampilkan "Halo Apa Kabar" | Arduino |

### CircuitPython (circuit-python/)

| No | File | Deskripsi | Platform |
|----|------|-----------|----------|
| CP1 | [cpS3EYE_espcamera_displayio.py](circuit-python/circuit-python-code/cpS3EYE_espcamera_displayio.py) | Kamera OV2640 via espcamera + tampil di LCD | CircuitPython |
| CP2 | [cpyS3EYE_LCD_color.py](circuit-python/circuit-python-code/cpyS3EYE_LCD_color.py) | Test warna LCD + animasi teks | CircuitPython |
| CP3 | [cpyS3EYE_turtle.py](circuit-python/circuit-python-code/cpyS3EYE_turtle.py) | Turtle graphics di LCD ESP32 | CircuitPython |
| CP4 | [py_turtle.py](circuit-python/circuit-python-code/py_turtle.py) | Turtle graphics di Desktop Python (pembanding) | Python 3 |

> Setiap folder memiliki `README.md` dengan penjelasan lengkap: pendahuluan, pin definition, cara kerja, alur berpikir, hasil, library, instalasi, dan troubleshooting.

---

## Catatan Hardware Penting

### LCD ST7789V — Backlight (GPIO 48)

Backlight menggunakan P-channel MOSFET (Q2 = AO3401A), bukan N-channel.

| Kode | Efek |
|------|------|
| `digitalWrite(48, LOW)` | Backlight **NYALA** |
| `digitalWrite(48, HIGH)` | Backlight **MATI** |

Intuisi N-channel (HIGH = ON) **tidak berlaku** di sini. Lihat [07-lcd-display/README.md](source-code-arduino/07-lcd-display/README.md) untuk penjelasan lengkap.

### LCD ST7789V — Cold Power-On (USB baru di-colokin)

Pada cold power-on, GPIO44 (LCD CS, active-LOW) mulai dari 0V → LCD ter-select sebelum firmware jalan → SPI state machine corrupt → layar hitam permanen. Fix wajib di `setup()`:

```cpp
#include <esp_system.h>
if (esp_reset_reason() == ESP_RST_POWERON) { delay(200); ESP.restart(); }
```

---

## Ringkasan Pin Definition Board

### Kamera OV2640
| Sinyal | GPIO | Sinyal | GPIO |
|--------|------|--------|------|
| XCLK | 15 | D0 (Y2) | 11 |
| SIOD | 4 | D1 (Y3) | 9 |
| SIOC | 5 | D2 (Y4) | 8 |
| VSYNC | 6 | D3 (Y5) | 10 |
| HREF | 7 | D4 (Y6) | 12 |
| PCLK | 13 | D5 (Y7) | 18 |
| PWDN | — | D6 (Y8) | 17 |
| RESET | — | D7 (Y9) | 16 |

### Mikrofon I2S (MSM261S4030H0)
| Sinyal | GPIO |
|--------|------|
| WS (LRCK) | 42 |
| SCK (BCK) | 41 |
| SD (DATA) | 2 |

### LCD ST7789V 240×240
| Sinyal | GPIO |
|--------|------|
| MOSI | 47 |
| SCK | 21 |
| CS | 44 |
| DC | 43 |
| RST | — (terhubung ke EN board) |
| BL | 48 (P-channel: LOW=ON) |

### SD Card (SDMMC 1-bit)
| Sinyal | GPIO |
|--------|------|
| CLK | 39 |
| CMD | 38 |
| D0 | 40 |

### LED & Tombol
| Komponen | GPIO |
|----------|------|
| LED | 3 |
| BOOT Button | 0 |
| Function Button | 1 (ADC) |

---

## Firmware & Tools

| Folder | Isi |
|--------|-----|
| [manufaktur-firmware/](manufaktur-firmware/) | Firmware bawaan pabrik V2.2 + panduan flash |
| [circuit-python/](circuit-python/) | Instalasi CircuitPython + firmware + bundle library |
| [skematik/](skematik/) | Schematic resmi ESP32-S3-EYE V2.2 |

---

## Referensi

1. Schematic: [SCH_ESP32-S3-EYE-MB_20211201_V2.2.pdf](https://github.com/prusa3d/Prusa-Firmware-ESP32-Cam/blob/master/doc/ESP32-S3-EYE-22/SCH_ESP32-S3-EYE-MB_20211201_V2.2.pdf)
2. ESP32-S3-EYE Getting Started Guide: http://vcc-gnd.cn/vcc_gnd/esp-who/src/commit/b454739d3ea4221ca96e17f88293faf625da4ff5/docs/en/get-started/ESP32-S3-EYE_Getting_Started_Guide.md
3. CircuitPython firmware: https://circuitpython.org/board/espressif_esp32s3_eye/
