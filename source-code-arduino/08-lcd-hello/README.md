# 08 — LCD Hello (Test Minimal)

## Pendahuluan

Program uji minimal LCD ST7789V — menampilkan teks "Halo Apa Kabar" dengan informasi board. Dibuat sebagai alat diagnostik untuk mengisolasi masalah layar hitam pada sketch 07, membuktikan bahwa kedua root cause (polaritas backlight + cold power-on) dapat diperbaiki dengan kode seminimal mungkin.

Tujuan: validasi cepat bahwa LCD berfungsi penuh setelah perbaikan root cause diterapkan.

---

## Pin Definition

| Sinyal | GPIO | Keterangan |
|--------|------|------------|
| MOSI | 47 | SPI Data |
| SCK | 21 | SPI Clock |
| CS | 44 | Chip Select (active-LOW) |
| DC | 43 | Data/Command |
| RST | -1 | Tidak ada — terhubung ke EN board |
| BL | 48 | Backlight (P-channel: LOW=ON) |

---

## Cara Kerja Program

1. **Pre-init** — CS dan DC di-set HIGH untuk mencegah LCD selection saat GPIO masih 0V
2. **Cold Power-On Fix** — Deteksi `ESP_RST_POWERON` → software restart untuk membersihkan state GPIO
3. **Backlight ON** — `digitalWrite(BL, LOW)` karena P-channel MOSFET
4. **SPI + LCD Init** — `SPI.begin()` hardware SPI, `tft.init(240, 240)`, `tft.setRotation(2)`
5. **Render Tampilan** — Background biru gelap, garis hias cyan, teks "Halo" (putih, size 3), "Apa Kabar?" (cyan, size 2), divider, info board (abu-abu)
6. **Serial Output** — Menampilkan reset reason untuk verifikasi cold power-on fix bekerja

---

## Alur Berpikir (Logic Flow)

```
SETUP:
  ├─ pinMode(CS, OUTPUT); digitalWrite(CS, HIGH)
  ├─ pinMode(DC, OUTPUT); digitalWrite(DC, HIGH)
  │
  ├─ IF esp_reset_reason() == ESP_RST_POWERON:
  │   ├─ delay(200)
  │   └─ ESP.restart()  → boot ke-2
  │
  ├─ delay(50)
  ├─ pinMode(BL, OUTPUT); digitalWrite(BL, LOW)  // P-ch: LOW=ON
  ├─ SPI.begin(SCK, -1, MOSI)
  ├─ tft.init(240, 240)
  ├─ tft.setRotation(2)
  │
  ├─ fillScreen(0x0841)           // biru gelap
  ├─ fillRect atas + bawah (cyan) // garis hias
  ├─ Text "Halo" (putih, size 3, center)
  ├─ Text "Apa Kabar?" (cyan, size 2, center)
  ├─ drawFastHLine (divider cyan)
  ├─ Text "YD-ESP32-S3-EYE" (abu)
  ├─ Text "LCD ST7789V" (abu)
  ├─ Text "240x240 SPI 3.3V" (abu)
  │
  ├─ Serial.begin(115200)
  ├─ Print reset reason
  └─ Print "LCD init OK"

LOOP:
  └─ (kosong)
```

### Nilai Reset Reason

| Nilai | Makro | Artinya |
|-------|-------|---------|
| 1 | `ESP_RST_POWERON` | Cold power-on → langsung restart |
| 2 | `ESP_RST_SW` | Software restart — normal, LCD init berhasil |

---

## Hasil

### Tampilan LCD

```
┌─────────────────────────────────┐
│▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄│  ← garis cyan
│                                 │
│             Halo                │  ← putih, size 3
│                                 │
│          Apa Kabar?             │  ← cyan, size 2
│  ─────────────────────────────  │  ← garis divider
│        YD-ESP32-S3-EYE          │  ← abu
│          LCD ST7789V            │
│      240x240  SPI  3.3V         │
│▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄│  ← garis cyan
└─────────────────────────────────┘
Background: biru gelap (0x0841)
```

### Serial Monitor Output

```
Reset reason: 2
LCD init OK — Halo Apa Kabar!
```

- Reset reason 1 = cold power-on (langsung di-restart)
- Reset reason 2 = software restart (boot normal, LCD init sukses)

---

## Library yang Digunakan

| Library | Instalasi | Keterangan |
|---------|-----------|------------|
| **Adafruit ST7789** | Library Manager | Driver LCD |
| **Adafruit GFX Library** | Library Manager | Graphics primitives |
| `SPI.h` | Built-in | Hardware SPI |
| `esp_system.h` | Built-in ESP32 | Reset reason detection |

---

## Cara Instal Library

1. Arduino IDE → **Tools → Manage Libraries**
2. Install `Adafruit ST7789` dan `Adafruit GFX Library`

**Arduino IDE Settings:**
- Board: ESP32S3 Dev Module
- USB Mode: Hardware CDC and JTAG
- PSRAM: OPI PSRAM

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Layar hitam | Pastikan `digitalWrite(TFT_BL, LOW)` — P-channel MOSFET |
| Layar hanya muncul saat tekan RST | Cold power-on fix belum diterapkan — cek reset reason di serial |
| Teks tidak muncul / aneh | Cek `setRotation(2)`, pastikan library Adafruit ST7789 terinstall |
| Serial Monitor kosong | Normal jika pakai USB-CDC — cek port yang benar di Device Manager |
