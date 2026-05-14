# 10 — IMU Cube (3D Wireframe on LCD)

## Pendahuluan

Visualisasi kubus 3D wireframe pada LCD ST7789V yang **berputar mengikuti kemiringan board** — saat board dimiringkan ke kiri, kubus menampilkan sisi kanan (seperti objek nyata yang diam di dunia). Data kemiringan dibaca dari akselerometer QMA7981 secara real-time.

> **Board:** YD-ESP32-S3-EYE
> **LCD:** ST7789V 240×240 SPI
> **Sensor:** QMA7981 3-axis accelerometer I²C (addr 0x12)

---

## Pin Definition

### LCD (SPI)

| Sinyal | GPIO | Keterangan |
|--------|------|------------|
| MOSI | 47 | SPI Data |
| SCK | 21 | SPI Clock |
| CS | 44 | Chip Select (active-LOW) |
| DC | 43 | Data/Command |
| RST | -1 | Terhubung ke EN board (no GPIO) |
| BL | 48 | Backlight — **P-channel MOSFET: LOW = ON** |

### Accelerometer (I²C)

| Sinyal | GPIO | Keterangan |
|--------|------|------------|
| SDA | 4 | I²C Data |
| SCL | 5 | I²C Clock |
| I2C Addr | 0x12 | Fixed address QMA7981 |

---

## Cara Kerja Program

1. **LCD Pre-init** — CS HIGH dulu, BL LOW (P-channel), cold-boot fix `ESP.restart()`
2. **Boot Splash** — teks "IMU CUBE" + progress bar sementara sensor inisialisasi
3. **QMA7981 Init** — soft reset → standby → konfigurasi ±8g / 128Hz → active mode
4. **Main Loop (~30 FPS)**:
   - Baca XYZ dari QMA7981
   - **Low-pass filter** (exponential moving average) untuk smoothing gerakan
   - **Normalisasi** vektor gravitasi (menghilang noise magnitudo)
   - Hitung sudut rotasi dari kemiringan: `angleX = -nay × 1.4`, `angleY = -nax × 1.4`
   - **Rotasi 3D** (Y lalu X) pada 8 vertex kubus
   - **Proyeksi perspektif** ke 2D screen koordinat
   - **Gambar** 12 edge wireframe + titik tengah

---

## Alur Berpikir (Logic Flow)

```
SETUP:
  ├─ LCD pre-init (CS HIGH, BL LOW, cold-boot fix)
  ├─ SPI.begin() + tft.init(240,240) + setRotation(2)
  ├─ Boot splash + progress bar
  ├─ I2C: soft-reset QMA7981
  ├─ Konfigurasi: ±8g range, 128Hz BW
  └─ Active mode

LOOP (setiap ~30ms):
  ├─ readXYZ(ax, ay, az)         → burst-read 6 byte I²C
  ├─ LOW-PASS FILTER:
  │     sax = sax×0.92 + ax×0.08
  │     say = say×0.92 + ay×0.08
  │     saz = saz×0.92 + az×0.08
  ├─ NORMALISE: n = sax,say,saz ÷ |g|
  ├─ ROTATION: angleX = -nay×1.4, angleY = -nax×1.4
  ├─ PROJECTION (per vertex):
  │     [x1,z1] = rotateY(x,z, angleY)
  │     [y2,z2] = rotateX(y1,z1, angleX)
  │     screen = centre + (x2,y2) × 280 / (z2 + 4.5)
  ├─ fillScreen(BLACK)
  ├─ FOR each edge: drawLine(v[a], v[b], CYAN)
  └─ fillCircle(centre, 2, WHITE)   // dot referensi
```

---

## Hasil

- Kubus 3D wireframe berwarna **CYAN** di tengah layar 240×240
- Saat board **datar di meja** → kubus tampak dari depan (near face)
- Saat board **dimiringkan** → kubus berotasi, menampilkan sisi sesuai sudut tilt
- **Dot putih** di tengah sebagai referensi
- Gerakan **halus** berkat low-pass filter (α = 0.08)

---

## Library yang Digunakan

| Library | Instalasi | Keterangan |
|---------|-----------|------------|
| **Adafruit ST7789** | Arduino Library Manager | Driver LCD ST7789V via SPI |
| **Adafruit GFX Library** | Arduino Library Manager | Graphics primitives (drawLine, fillCircle, fillScreen) |
| `Wire.h` | Built-in ESP32 | I²C master (QMA7981) |
| `SPI.h` | Built-in ESP32 | Hardware SPI (LCD) |
| `esp_system.h` | Built-in ESP32 | `esp_reset_reason()` cold-boot fix |

---

## Arduino IDE Settings

| Setting | Nilai |
|---------|-------|
| Board | ESP32S3 Dev Module |
| USB Mode | Hardware CDC and JTAG (default) |
| USB CDC On Boot | **Enabled** |
| PSRAM | OPI PSRAM |
| Flash Size | 8MB (64Mb) |
| Partition Scheme | 8M with spiffs (3MB APP/1.5MB SPIFFS) |
| Upload Speed | 921600 |

## Compile & Upload via arduino-cli

```powershell
arduino-cli compile --fqbn "esp32:esp32:esp32s3:FlashSize=8M,PSRAM=opi,CDCOnBoot=cdc,PartitionScheme=default_8MB" "source-code-arduino/10-imu-cube"
arduino-cli upload -p COM5 --fqbn "esp32:esp32:esp32s3:FlashSize=8M,PSRAM=opi,CDCOnBoot=cdc,PartitionScheme=default_8MB" "source-code-arduino/10-imu-cube"
```

---

## Parameter yang Bisa Di-tuning

| Konstanta | Nilai Default | Fungsi |
|-----------|---------------|--------|
| `SENSITIVITY` | 1.4 | Gain rotasi — lebih besar = kubus lebih responsif |
| `SMOOTH` | 0.08 | Low-pass filter — lebih kecil = lebih smooth tapi lebih lambat |
| `CUBE_SIZE` | 280.0 | Faktor skala proyeksi — lebih besar = kubus lebih besar |
| `PERSP_DIST` | 4.5 | Jarak perspektif — lebih kecil = efek perspektif lebih kuat |

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Layar gelap | Pastikan `digitalWrite(TFT_BL, LOW)` — P-channel MOSFET: LOW = ON |
| Kubus tidak bergerak | Cek koneksi I²C — jalankan `09-i2c-scanner` untuk verifikasi |
| Kubus terlalu sensitif | Turunkan `SENSITIVITY` ke 0.8 – 1.0 |
| Kubus lambat merespon | Naikkan `SMOOTH` ke 0.12 – 0.18 |
| Layar hanya muncul saat tekan RST | Cold power-on fix belum jalan — pastikan kode `ESP.restart()` ada |
