# 08 — LCD Hello (Test Minimal)

Program minimal: tampilkan "Halo Apa Kabar" di LCD ST7789V 240×240.

Sketch ini dibuat sebagai **alat diagnostik** untuk mengisolasi masalah layar hitam di sketch 07 — membuktikan bahwa kedua root cause dapat diperbaiki dengan kode seminimal mungkin sebelum diterapkan ke sketch yang lebih kompleks.

---

## Tampilan

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

---

## Root Cause & Fix

### Gejala yang dialami

Layar selalu hitam setelah USB di-colokin. Konten hanya muncul **saat tombol RST ditekan dan ditahan**. Ini berlaku untuk semua sketch LCD yang pernah dicoba.

---

### Root Cause #1 — Backlight polarity terbalik (penyebab utama)

**Q2 = AO3401A** adalah **P-channel MOSFET** (high-side switch), bukan N-channel.

| Kode | GPIO48 | VGS | MOSFET | Backlight |
|------|--------|-----|--------|-----------|
| `digitalWrite(TFT_BL, HIGH)` ❌ | HIGH | 0V | OFF | **mati** |
| `digitalWrite(TFT_BL, LOW)` ✅  | LOW  | −3.3V | **ON** | **NYALA** |

LCD **sudah menggambar dengan benar sejak awal** — backlight saja yang dimatikan oleh kode yang salah.

Bukti: saat RST ditekan, GPIO48 masuk kondisi Hi-Z → gate float ke GND → VGS = −3.3V → MOSFET ON → backlight nyala → konten terlihat jelas.

**Fix:**
```cpp
pinMode(TFT_BL, OUTPUT);
digitalWrite(TFT_BL, LOW);   // P-channel: LOW = ON
```

---

### Root Cause #2 — Cold power-on: GPIO start dari 0V

Pada cold power-on (USB baru di-colokin), semua GPIO ESP32-S3 mulai dari **0V** sebelum firmware berjalan.

- GPIO44 = LCD CS, active-LOW → 0V = LOW = **LCD ter-select sebelum `setup()` dipanggil**
- Saat `SPI.begin()` dipanggil, SCK (GPIO21) bertransisi → LCD menerima noise SPI dalam kondisi ter-select
- SPI state machine LCD **corrupt** → `tft.init()` gagal → layar putih/hitam permanen

Saat RST ditekan: semua GPIO ke Hi-Z → CS tidak ter-select → LCD reset → init berhasil.

**Fix:**
```cpp
#include <esp_system.h>

// Deteksi cold power-on, lakukan software restart
if (esp_reset_reason() == ESP_RST_POWERON) {
    delay(200);       // tunggu power stabil
    ESP.restart();    // GPIO ke Hi-Z = identik dengan tekan RST hardware
}
// Boot kedua: ESP_RST_SW → GPIO sudah Hi-Z → LCD clean → init berhasil ✓
```

---

### Urutan setup() yang benar

```cpp
void setup() {
  // 1. CS HIGH dulu — cegah LCD selection saat GPIO masih 0V
  pinMode(TFT_CS, OUTPUT);
  digitalWrite(TFT_CS, HIGH);
  pinMode(TFT_DC, OUTPUT);
  digitalWrite(TFT_DC, HIGH);

  // 2. Cold power-on fix
  if (esp_reset_reason() == ESP_RST_POWERON) {
    delay(200);
    ESP.restart();
  }

  // 3. Backlight ON (setelah restart, GPIO sudah bersih)
  delay(50);
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, LOW);   // P-channel: LOW = ON

  // 4. SPI dan LCD init
  SPI.begin(TFT_SCLK, -1, TFT_MOSI);
  tft.init(240, 240);
  tft.setRotation(2);
}
```

---

## Arduino IDE Settings

| Setting          | Nilai                      |
|------------------|----------------------------|
| Board            | ESP32S3 Dev Module         |
| USB Mode         | Hardware CDC and JTAG      |
| PSRAM            | OPI PSRAM                  |
| Upload Speed     | 921600                     |

---

## Cara Pakai

1. Upload sketch
2. LCD tampil **langsung tanpa perlu tekan RST**
   - Ada jeda ~200ms saat boot pertama (cold power-on) untuk software restart
3. Serial Monitor (115200 baud) menampilkan:
   ```
   Reset reason: 2
   LCD init OK — Halo Apa Kabar!
   ```
   - Reset reason 1 = `ESP_RST_POWERON` (cold power-on, langsung restart)
   - Reset reason 2 = `ESP_RST_SW` (setelah software restart — normal)

---

## Hubungan dengan 07-lcd-display

Sketch ini dibuat saat debugging 07-lcd-display. Tujuan:
- Isolasi masalah: apakah init LCD yang salah atau kode slideshow yang bermasalah?
- Buktikan fix minimal bekerja sebelum diterapkan ke sketch kompleks
- Referensi untuk proyek LCD berikutnya di board ini

Kedua fix yang ditemukan di sketch ini kemudian diterapkan ke 07-lcd-display v1.5.
