# 07 — LCD Display (ST7789V 240×240)

## Pendahuluan

Demo slideshow komprehensif pada LCD 1.3" ST7789V bawaan YD-ESP32-S3-EYE. Menampilkan 5 layar bergantian: boot splash, demo warna, bentuk geometri, info board, dan animasi bola bouncing.

Program ini juga mendokumentasikan proses debugging ekstensif yang menemukan **dua root cause** penyebab layar hitam pada board ini: (1) polaritas backlight P-channel MOSFET terbalik, (2) cold power-on SPI state machine corruption.

> **Pin terkonfirmasi** dari skematik resmi `SCH_ESP32-S3-EYE-MB_20211201_V2.2.pdf` (J9 connector) dan pengujian nyata. Sub-board: **YD-ESP32Z-S3-EYE-SUB V1.1**

---

## Pin Definition

| Sinyal | GPIO | Keterangan |
|--------|------|------------|
| MOSI | 47 | SPI Data (Master Out Slave In) |
| SCK | 21 | SPI Clock |
| CS | 44 | Chip Select (active-LOW) — default UART0 RX |
| DC | 43 | Data/Command — default UART0 TX |
| RST | -1 | Tidak ada GPIO RST — terhubung ke EN board |
| **BL** | **48** | **Backlight — P-channel MOSFET: LOW = ON** |

---

## Cara Kerja Program

1. **Pre-init Sequence** (sebelum SPI):
   - `CS = HIGH` — cegah LCD ter-select saat GPIO masih 0V
   - `BL = LOW` — nyalakan backlight (P-channel MOSFET)
2. **Cold Power-On Fix** — `esp_reset_reason() == ESP_RST_POWERON` → `ESP.restart()` (software restart untuk reset GPIO ke Hi-Z)
3. **SPI Init** — `SPI.begin(SCK, -1, MOSI)` — hardware SPI (jauh lebih cepat dari software SPI)
4. **LCD Init** — `tft.init(240, 240)` + `tft.setRotation(2)`
5. **Slideshow Loop** (berjalan di `setup()`, bukan `loop()`):

   | Urutan | Layar | Fungsi | Durasi |
   |--------|-------|--------|--------|
   | 1 | `screenBoot()` | Nama board, versi, lingkaran OK | 2.5 detik |
   | 2 | `screenColor()` | 8 warna dasar grid 4×2 | 2 detik |
   | 3 | `screenShapes()` | Rect, circle, triangle, rounded rect, garis diagonal | 2.5 detik |
   | 4 | `screenInfo()` | Tabel spesifikasi hardware | 3 detik |
   | 5 | `screenBounce()` | Bola memantul dengan warna berubah tiap tepi | 4 detik |

---

## Alur Berpikir (Logic Flow)

```
SETUP:
  ├─ pinMode(CS, OUTPUT); digitalWrite(CS, HIGH)
  │   └─ Cegah LCD selection saat GPIO 0V
  ├─ pinMode(BL, OUTPUT); digitalWrite(BL, LOW)
  │   └─ P-channel MOSFET: LOW = backlight ON
  ├─ IF esp_reset_reason() == ESP_RST_POWERON:
  │   ├─ delay(200)
  │   └─ ESP.restart()  → boot ulang, GPIO ke Hi-Z
  ├─ SPI.begin(SCK, -1, MOSI)   // hardware SPI, sekali saja
  ├─ tft.init(240, 240)
  ├─ tft.setRotation(2)
  └─ WHILE true:  // slideshow infinite
      ├─ screenBoot()    → delay(2500)
      ├─ screenColor()   → delay(2000)
      ├─ screenShapes()  → delay(2500)
      ├─ screenInfo()    → delay(3000)
      └─ screenBounce(4000)

LOOP:
  └─ (kosong — slideshow di setup)
```

### screenBounce() Sub-flow
```
  ├─ bx=120, by=120, r=18, dx=3, dy=2
  └─ WHILE millis() - start < durationMs:
      ├─ fillCircle(bx, by, r, BLACK)   // hapus posisi lama
      ├─ bx += dx; by += dy
      ├─ IF bx-r < 0    → pantul kanan,  warna MERAH
      ├─ IF bx+r > 239  → pantul kiri,   warna HIJAU
      ├─ IF by-r < 0    → pantul bawah,  warna KUNING
      ├─ IF by+r > 239  → pantul atas,   warna CYAN
      ├─ fillCircle(bx, by, r, ballColor)  // gambar posisi baru
      └─ delay(12)
```

---

## Hasil

LCD menampilkan slideshow 5 layar yang berulang terus-menerus:

1. **Boot Splash** — "YD-ESP32 S3-EYE", "LCD ST7789V", lingkaran oranye "OK", garis aksen cyan
2. **Color Blocks** — Grid 4×2 warna: RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, WHITE, ORANGE
3. **Shapes Demo** — Rectangle biru, lingkaran merah, segitiga hijau, rounded rect magenta, garis diagonal cyan
4. **Board Info** — Tabel: MCU ESP32-S3, PSRAM 8MB OPI, Flash 8MB, Cam OV2640, LCD ST7789V, Mic I2S 16kHz, SD SDMMC 1-bit, WiFi 2.4GHz BLE5
5. **Bounce Animation** — Bola memantul dengan warna berubah setiap menyentuh tepi

Serial Monitor menampilkan progres siklus:
```
╔══════════════════════════════════╗
║  ESP32-S3-EYE  LCD ST7789V Test ║
║  BL=LOW(P-ch)  v1.5             ║
╚══════════════════════════════════╝

[Siklus 1]
  [1] Boot splash
  [2] Color blocks
  [3] Shapes demo
  [4] Board info
  [5] Bounce animation
```

---

## Library yang Digunakan

| Library | Instalasi | Keterangan |
|---------|-----------|------------|
| **Adafruit ST7789** | Arduino Library Manager | Driver LCD ST7789V via SPI |
| **Adafruit GFX Library** | Arduino Library Manager | Graphics primitives (teks, bentuk, warna) |
| `SPI.h` | Built-in | Hardware SPI komunikasi |
| `esp_system.h` | Built-in ESP32 | `esp_reset_reason()` untuk cold power-on fix |

---

## Cara Instal Library

1. Buka Arduino IDE
2. **Tools → Manage Libraries**
3. Cari dan install:
   - `Adafruit ST7789` (by Adafruit)
   - `Adafruit GFX Library` (by Adafruit)

**Arduino IDE Settings:**

| Setting | Nilai |
|---------|-------|
| Board | ESP32S3 Dev Module |
| USB Mode | **Hardware CDC and JTAG** (wajib — GPIO 43/44 dipakai LCD) |
| PSRAM | OPI PSRAM |
| Upload Speed | 921600 |

> USB Mode wajib Hardware CDC and JTAG karena GPIO 43/44 (UART0 TX/RX default) digunakan oleh LCD. Serial Monitor akan tetap berfungsi via USB-CDC.

---

## Root Cause & Fix (versi 1.5 — Terkonfirmasi)

### Root Cause #1 — Backlight Polarity (P-channel MOSFET)

**Komponen:** Q2 = AO3401A, P-channel MOSFET (high-side switch).

| GPIO48 | VGS | MOSFET | Backlight |
|--------|-----|--------|-----------|
| `LOW` | -3.3V | **ON** | **NYALA** |
| `HIGH` | 0V | OFF | MATI |

Semua versi kode sebelumnya menggunakan `digitalWrite(TFT_BL, HIGH)` — ini mematikan backlight. LCD sebenarnya sudah menggambar dengan benar sejak awal.

**Fix:** `digitalWrite(TFT_BL, LOW);`

### Root Cause #2 — Cold Power-On GPIO Corruption

Saat USB baru di-colok, semua GPIO mulai dari 0V. GPIO44 (CS, active-LOW) = LOW → LCD ter-select sebelum firmware jalan. Saat `SPI.begin()` dipanggil, SCK bertransisi → LCD menerima noise → SPI state machine corrupt → init gagal.

**Fix:**
```cpp
if (esp_reset_reason() == ESP_RST_POWERON) {
    delay(200);
    ESP.restart();  // GPIO ke Hi-Z = identik tekan RST
}
```

### Urutan setup() yang Benar

```cpp
void setup() {
  pinMode(TFT_CS, OUTPUT);  digitalWrite(TFT_CS, HIGH);   // 1. CS HIGH
  pinMode(TFT_BL, OUTPUT);  digitalWrite(TFT_BL, LOW);    // 2. BL ON (P-ch)
  if (esp_reset_reason() == ESP_RST_POWERON) {             // 3. Cold fix
    delay(200); ESP.restart();
  }
  delay(50);
  SPI.begin(TFT_SCLK, -1, TFT_MOSI);                      // 4. SPI init
  tft.init(240, 240);                                     // 5. LCD init
  tft.setRotation(2);
}
```

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Layar tetap gelap/hitam | Pastikan `digitalWrite(TFT_BL, LOW)` — P-channel MOSFET: LOW = ON |
| Layar hanya muncul saat tekan RST | Tambahkan cold power-on fix `ESP.restart()` |
| Teks mirror/terbalik | Pastikan `setRotation(2)`, bukan `setRotation(0)` |
| Animasi sangat lambat | Gunakan Hardware SPI: `SPI.begin(SCK, -1, MOSI)` |
| Layar hitam setelah beberapa siklus | Jangan panggil `SPI.begin()` lebih dari sekali |
| Layar putih solid | Cek pin MOSI/SCK (GPIO 47 dan 21) |
| Serial Monitor kosong | Normal — board pakai USB-CDC; GPIO 43/44 dipakai LCD |
