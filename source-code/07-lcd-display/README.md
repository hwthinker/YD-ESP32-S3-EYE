# 07 — LCD Display (ST7789V 240×240)

Demo slideshow pada LCD 1.3" ST7789V bawaan ESP32-S3-EYE. Menampilkan boot screen, demo warna, bentuk geometri, info board, dan animasi bola bouncing.

> **Pin terkonfirmasi** dari skematik resmi `SCH_ESP32-S3-EYE-MB_20211201_V2.2.pdf` (J9 connector) dan hasil pengujian nyata.
> Sub-board: **YD-ESP32Z-S3-EYE-SUB V1.1**

---

## Hardware — Pin LCD ST7789V

| Sinyal  | GPIO | Keterangan |
|---------|------|------------|
| MOSI    | 47   | SPI Data   |
| SCK     | 21   | SPI Clock  |
| CS      | 44   | Chip Select (default: UART0 RX — aman karena board pakai USB-CDC) |
| DC      | 43   | Data/Command (default: UART0 TX — sama seperti CS) |
| RST     | —    | Tidak ada GPIO RST — terhubung ke EN board (dikonfirmasi dari CircuitPython `board.c`: RST = NULL) |
| **BL**  | **48** | **Backlight — wajib `LOW` agar layar menyala (Q2 = AO3401A P-channel MOSFET)** |

---

## Library yang Diperlukan

Install keduanya dari **Arduino IDE → Tools → Manage Libraries**:

| Library | Pencarian di Library Manager |
|---------|------------------------------|
| **Adafruit ST7789** | `Adafruit ST7789` |
| **Adafruit GFX Library** | `Adafruit GFX` |

---

## Arduino IDE Settings

| Setting              | Nilai                                   |
|----------------------|-----------------------------------------|
| Board                | ESP32S3 Dev Module                      |
| Port                 | COM5 (sesuaikan)                        |
| Upload Speed         | 921600                                  |
| USB Mode             | **Hardware CDC and JTAG** ← penting!    |
| PSRAM                | OPI PSRAM                               |

> **USB Mode wajib Hardware CDC and JTAG** karena GPIO 43/44 (UART0 TX/RX default) dipakai oleh LCD. Kalau pakai UART CDC, Serial Monitor tidak akan muncul — tapi itu normal, LCD tetap bekerja.

---

## Cara Upload & Pakai

1. Install library **Adafruit ST7789** dan **Adafruit GFX** dari Library Manager
2. Buka `07-lcd-display.ino` di Arduino IDE
3. Set board dan port (lihat tabel di atas)
4. Klik **Upload**
5. LCD langsung menampilkan demo slideshow tanpa perlu tekan RST

---

## Isi Demo Slideshow

| Urutan | Tampilan | Durasi |
|--------|----------|--------|
| 1 | **Boot splash** — nama board, versi, lingkaran OK | 2.5 detik |
| 2 | **Color blocks** — 8 warna dasar dalam grid 4×2 | 2 detik |
| 3 | **Shapes demo** — persegi, lingkaran, segitiga, rounded rect, garis | 2.5 detik |
| 4 | **Board info** — tabel spesifikasi hardware lengkap | 3 detik |
| 5 | **Bounce animation** — bola memantul dengan warna berubah | 5 detik |

Setelah selesai, slideshow diulang dari awal (infinite loop).

---

## Root Cause & Fix (v1.5 — Terkonfirmasi)

### Gejala awal

Layar selalu gelap/hitam setelah USB di-colokin. Konten hanya muncul **saat tombol RST ditekan dan ditahan**. Setelah RST dilepas, layar kembali hitam.

### Root Cause #1 — Backlight polarity terbalik

**Komponen:** Q2 = **AO3401A**, P-channel MOSFET (high-side switch), bukan N-channel.

| GPIO48 | VGS | MOSFET | Backlight |
|--------|-----|--------|-----------|
| `LOW`  | −3.3V | **ON** | **NYALA** ✓ |
| `HIGH` | 0V  | OFF    | mati ✗ |

Semua versi kode sebelumnya menggunakan `digitalWrite(TFT_BL, HIGH)` — ini justru **mematikan** backlight karena karakteristik P-channel MOSFET kebalikan dari N-channel.

LCD sebenarnya **sudah menggambar dengan benar sejak awal** — hanya backlight yang dimatikan oleh kode yang salah.

**Clue yang memecahkan kasus:** Foto layar saat RST ditekan lama menampilkan semua konten slideshow dengan jelas → LCD berfungsi sempurna, hanya backlight yang off. Saat RST: GPIO48 Hi-Z → gate float ke GND → VGS = −3.3V → MOSFET ON → backlight nyala.

**Fix:**
```cpp
pinMode(TFT_BL, OUTPUT);
digitalWrite(TFT_BL, LOW);   // P-channel: LOW = ON (bukan HIGH!)
```

### Root Cause #2 — Cold power-on GPIO start dari 0V

Pada cold power-on (USB baru di-colokin), semua GPIO ESP32-S3 mulai dari **0V** sebelum firmware berjalan.

GPIO44 = LCD CS, active-LOW → 0V = LOW = **LCD ter-select** sebelum `setup()` dipanggil.

Selama proses booting, SPI clock (GPIO21) bertransisi saat `SPI.begin()` dipanggil → LCD menerima sinyal noise dalam kondisi ter-select → **SPI state machine LCD corrupt** → init gagal → layar putih/hitam permanen.

Saat RST ditekan: GPIO ke Hi-Z (floating) → CS tidak ter-select → LCD reset ke kondisi bersih → init berhasil.

**Fix:**
```cpp
#include <esp_system.h>

// Di awal setup(), SEBELUM SPI.begin():
if (esp_reset_reason() == ESP_RST_POWERON) {
    delay(200);       // beri waktu power stabil
    ESP.restart();    // software restart = GPIO Hi-Z = identik dengan tekan RST hardware
}
// Boot kedua masuk ESP_RST_SW → GPIO sudah Hi-Z → LCD clean → init berhasil
```

### Urutan fix yang benar di `setup()`

```cpp
void setup() {
  // 1. CS HIGH dulu — hentikan LCD selection saat GPIO masih 0V
  pinMode(TFT_CS, OUTPUT);
  digitalWrite(TFT_CS, HIGH);

  // 2. Backlight ON (P-channel: LOW = ON)
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, LOW);

  // 3. Cold power-on fix
  if (esp_reset_reason() == ESP_RST_POWERON) {
    delay(200);
    ESP.restart();
  }

  // 4. SPI dan LCD init (dipanggil SEKALI SAJA, tidak di loop)
  delay(50);
  SPI.begin(TFT_SCLK, -1, TFT_MOSI);
  tft.init(240, 240);
  tft.setRotation(2);
}
```

---

## Debugging Journey — False Leads yang Dicoba

Sebelum menemukan root cause yang sebenarnya, beberapa hal dicoba (dan bukan penyebabnya):

| Yang Dicoba | Dugaan saat itu | Hasil | Kesimpulan |
|-------------|-----------------|-------|------------|
| `TFT_RST = 46` (IO46 sebagai RST) | LCD butuh RST GPIO | Tidak berubah | RST = NULL, terhubung ke EN board |
| `TFT_RST = 45`, `-1` | Berbagai opsi RST | Tidak berubah | Dikonfirmasi dari CircuitPython `board.c` |
| `tft.init(240, 240, SPI_MODE0)` | SPI mode salah | Tidak berubah | Mode tidak relevan |
| `SPI.begin()` dipindah dari loop ke setup | Panggil berulang menyebabkan glitch CS | Tidak memperbaiki layar hitam utama | Valid sebagai code improvement, bukan root cause |
| Ganti kabel / cek koneksi | Hardware fault | Tidak berubah | Hardware benar (CircuitPython membuktikan) |
| **Flash CircuitPython** | Verifikasi hardware | **Layar muncul langsung!** | ← Ini yang membuktikan hardware 100% OK, masalah di software |

Setelah CircuitPython bekerja sempurna → fokus ke software → foto layar saat RST ditekan → backlight ternyata mati → P-channel MOSFET ditemukan sebagai root cause.

---

## Lainnya yang Diperbaiki (Valid tapi Bukan Root Cause Utama)

| Gejala | Penyebab | Fix |
|--------|----------|-----|
| Teks terbalik + mirror | `setRotation(0)` salah untuk orientasi LCD ini | `setRotation(2)` |
| Animasi sangat lambat / freeze setelah layar 4 | Software SPI — `fillCircle` tiap frame butuh beberapa detik | Hardware SPI via `SPI.begin(TFT_SCLK, -1, TFT_MOSI)` |
| Layar hitam setelah siklus ke-1 dalam loop | `SPI.begin()` dipanggil ulang → glitch CS | Panggil `SPI.begin()` **sekali saja** di `setup()` |

---

## Troubleshoot

| Masalah | Solusi |
|---------|--------|
| Layar tetap gelap/hitam | Pastikan `digitalWrite(TFT_BL, LOW)` — Q2 AO3401A adalah **P-channel MOSFET**, LOW = ON |
| Layar hanya muncul saat tekan RST | Tambahkan cold power-on fix: `if (esp_reset_reason() == ESP_RST_POWERON) { delay(200); ESP.restart(); }` |
| Teks masih mirror | Pastikan `setRotation(2)`, bukan `setRotation(0)` |
| Animasi sangat lambat | Gunakan **Hardware SPI**: konstruktor 3 argumen + `SPI.begin(TFT_SCLK, -1, TFT_MOSI)` |
| Layar hitam setelah beberapa siklus | Jangan panggil `SPI.begin()` lebih dari sekali |
| Layar putih solid | Cek pin MOSI/SCK (GPIO 47 dan 21) |
| Serial Monitor kosong | Normal — board pakai USB-CDC; GPIO 43/44 dipakai LCD |
