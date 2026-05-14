# CircuitPython Scripts for YD-ESP32-S3-EYE

## Pendahuluan

Kumpulan script CircuitPython untuk menguji dan mendemonstrasikan kemampuan YD-ESP32-S3-EYE menggunakan CircuitPython 9.2.9. Mencakup uji coba LCD (warna + turtle graphics) dan kamera OV2640 via modul `espcamera`.

> **Firmware:** `adafruit-circuitpython-espressif_esp32s3_eye-en_US-9.2.9.bin` (tersedia di folder `../circuitpython-firmware/`)

> ⚠️ **Catatan Kompatibilitas Firmware:**
> | Versi | Status | Keterangan |
> |-------|--------|------------|
> | 8.x | ✅ Work | |
> | 9.x (tested: 9.2.9) | ✅ Work | **Recommended** |
> | 10.2 | ❌ Not Working | LCD blank |
> | 10.3 alpha | ❌ Not Working | LCD blank |
>
> **Gunakan 9.2.9** — download firmware di folder `../circuitpython-firmware/`

---

## Install Firmware CircuitPython

### Langkah 1: Install esptool

```powershell
pip install esptool
```

### Langkah 2: Masuk Bootloader Mode

Board harus dalam **bootloader mode** sebelum bisa di-flash. Kalau board masih dalam mode normal (CDC ACM / JTAG USB), esptool tidak bisa konek.

Cara masuk bootloader mode:

1. Tekan dan **tahan** tombol **BOOT**
2. Tekan dan lepas tombol **RESET** (sambil tetap tahan BOOT)
3. Lepas tombol **BOOT**

Board sekarang dalam bootloader mode — siap di-flash.

### Langkah 3: Cek COM Port

**Windows:** Buka Device Manager → Ports (COM & LPT) → catat COM port yang muncul (contoh: `COM5`).

> ⚠️ COM port di komputer kamu kemungkinan berbeda. Selalu cek Device Manager sebelum flash.

**Linux:** 
```bash
tail -f /var/log/syslog | grep tty
# Colok board → lihat port yang muncul, biasanya /dev/ttyUSB0 atau /dev/ttyACM0
```

### Langkah 4: Hapus Firmware Lama

```powershell
# Windows (ganti COM5 sesuai port kamu)
esptool --port COM5 erase_flash

# Linux
esptool --port /dev/ttyUSB0 erase-flash
```

### Langkah 5: Flash Firmware Baru

```powershell
# Windows
esptool --port COM5 --baud 460800 write-flash -z 0x0 adafruit-circuitpython-espressif_esp32s3_eye-en_US-9.2.9.bin

# Linux
esptool --port /dev/ttyUSB0 --baud 460800 write-flash -z 0x0 adafruit-circuitpython-espressif_esp32s3_eye-en_US-9.2.9.bin
```

> File firmware tersedia di folder `../circuitpython-firmware/`

### Langkah 6: Verifikasi

Setelah flash selesai, tekan tombol **RESET**. Drive `CIRCUITPY` akan muncul di File Explorer (Windows) atau di `/media/` (Linux). Kalau muncul — firmware berhasil terinstall. ✅

---

## Pin Definition

Board YD-ESP32-S3-EYE menggunakan pin definition bawaan CircuitPython (`board.DISPLAY` dll). Pin mapping otomatis ditangani oleh firmware CircuitPython untuk board `espressif_esp32s3_eye`.

| Peripheral    | Interface         | Keterangan                                 |
| ------------- | ----------------- | ------------------------------------------ |
| LCD ST7789V   | SPI via displayio | `board.DISPLAY` — 240×240, rotasi otomatis |
| Kamera OV2640 | espcamera         | Modul built-in CircuitPython               |
| Backlight     | GPIO 48           | Dikelola otomatis oleh `board.DISPLAY`     |

---

## Cara Kerja Program

### 1. cpyS3EYE_LCD_color.py — LCD Color Cycling Test

1. Buat background putih (`displayio.Bitmap` + `Palette`)
2. Buat layer warna di atasnya (1px margin)
3. Tambahkan label teks "Hello" + nama board
4. Animasi scale teks: 1x → 2x → 3x (masing-masing 2 detik)
5. **Loop infinite**: cycling warna (RED → GREEN → BLUE → WHITE → BLACK), teks menampilkan nama warna, warna teks di-XOR dengan `0xFFFFFF` untuk kontras

### 2. cpyS3EYE_turtle.py — Turtle Graphics

1. Import `adafruit_turtle` — implementasi turtle graphics untuk displayio
2. Draw 20 rotated squares: setiap square di-scale 1/1.2 dan di-rotasi 12.5° dari sebelumnya
3. White pen di atas background hitam (default)
4. Hasil: pola nested rotated squares geometris

### 3. cpS3EYE_espcamera_displayio.py — Kamera + LCD

1. Inisialisasi kamera dengan `espcamera.Camera()` — auto-detect OV2640
2. Konfigurasi: RGB565, 240×240, `RGB565_SWAPPED` colorspace
3. Report semua setting kamera ke serial console
4. **Loop**: `cam.frame_available` → `cam.take()` → set bitmap TileGrid → refresh LCD
5. Live preview kamera di LCD, ~8-10 fps

---

## Alur Berpikir (Logic Flow)

### LCD Color Test

```
START:
  ├─ display = board.DISPLAY
  ├─ Buat bgGroup (displayio.Group)
  ├─ Buat bg_bitmap putih → bg_sprite → append bgGroup
  ├─ Buat color_bitmap → color_sprite → append bgGroup
  ├─ Buat text_group dengan Label "Hello" + board name
  ├─ Animasi scale: 1 → delay(2s) → 2 → delay(2s) → 3
  └─ LOOP FOREVER:
      └─ FOR each (color, name) in colorSet:
          ├─ color_palette[0] = color
          ├─ text_area.text = name
          ├─ text_area.color = color XOR 0xFFFFFF
          └─ delay(2s)
```

### Turtle Graphics

```
START:
  ├─ turtle = Turtle(board.DISPLAY)
  ├─ FOR i = 0..19:
  │   ├─ FOR j = 0..3:
  │   │   └─ forward(200 / scale)
  │   │       right(90)
  │   ├─ right(12.5)
  │   └─ scale *= 1.2
  └─ END (gambar tetap di layar)
```

### ESP Camera + Display

```
START:
  ├─ cam = espcamera.Camera(...)
  ├─ Report all camera settings to serial
  ├─ Buat displayio Group + Bitmap + TileGrid
  └─ LOOP:
      ├─ IF cam.frame_available:
      │   └─ cam.take(1, bitmap)  // capture ke bitmap displayio
      └─ refresh (otomatis oleh displayio)
```

---

## Hasil

### LCD Color Test

LCD menampilkan warna berganti setiap 2 detik: RED → GREEN → BLUE → WHITE → BLACK (berulang). Teks "RED"/"GREEN"/dst ditampilkan dengan warna kontras.

### Turtle Graphics

LCD menampilkan pola 20 persegi bersarang yang dirotasi, membentuk spiral geometris.

### ESP Camera

LCD menampilkan live preview dari kamera OV2640. Serial console menampilkan detail konfigurasi kamera:

```
espcamera settings:
  frame_size: 240x240
  pixel_format: RGB565
  ...
```

---

## Library yang Digunakan

### CircuitPython (ada di bundle Adafruit)

| Library                 | Fungsi                          | Digunakan oleh                   |
| ----------------------- | ------------------------------- | -------------------------------- |
| `adafruit_display_text` | Label teks di LCD               | `cpyS3EYE_LCD_color.py`          |
| `adafruit_bitmap_font`  | Dependency display_text         | (otomatis)                       |
| `adafruit_turtle`       | Turtle graphics untuk displayio | `cpyS3EYE_turtle.py`             |
| `adafruit_espcamera`    | Driver kamera OV2640            | `cpS3EYE_espcamera_displayio.py` |

---

## Cara Install Library

### ✅ Cara Recommended: `circup` (Online)

`circup` adalah package manager resmi Adafruit untuk CircuitPython. Otomatis download library yang kompatibel dengan versi firmware di board dan langsung install ke `CIRCUITPY/lib/`.

```powershell
# Install circup (sekali saja)
pip install circup

# Colok board, tunggu CIRCUITPY muncul, lalu:
circup install adafruit_display_text adafruit_turtle adafruit_bitmap_font
```

Tidak perlu cari bundle, tidak perlu khawatir versi `.mpy` incompatible — `circup` handle semua otomatis.

---

### 🔌 Alternatif Offline

Gunakan salah satu cara berikut jika tidak ada koneksi internet. Folder `lib/` di repo ini berisi backup library yang diperlukan.

#### Cara 1: Copy Langsung via File Explorer / xcopy

Colok board → drive `CIRCUITPY` muncul → copy folder `lib/` dari repo ke drive:

```powershell
xcopy lib\* H:\lib\ /E /Y
```

> Ganti `H:\` dengan drive letter CIRCUITPY yang muncul di komputer kamu.

#### Cara 2: Upload via `mpremote`

```powershell
mpremote fs cp -r lib/adafruit_display_text :lib/adafruit_display_text
mpremote fs cp -r lib/adafruit_bitmap_font :lib/adafruit_bitmap_font
mpremote fs cp lib/adafruit_turtle.py :lib/adafruit_turtle.py
```

Tidak perlu tahu drive letter — `mpremote` auto-detect board via USB serial.

---

## Cara Menjalankan Program

### Testing Cepat (tidak tersimpan di board)

```powershell
mpremote run 01-cpS3EYE_espcamera_displayio.py
mpremote run 02-cpyS3EYE_LCD_color.py
mpremote run 03-cpyS3EYE_turtle.py
```

Program dieksekusi langsung dari PC ke RAM board. Setelah board di-reset, program hilang. Cocok untuk development dan debugging.

### Install Permanen (auto-run saat boot)

Copy program ke drive CIRCUITPY dengan nama `code.py`:

```powershell
copy .\01-cpS3EYE_espcamera_displayio.py H:\code.py
copy .\02-cpyS3EYE_LCD_color.py H:\code.py
copy .\03-cpyS3EYE_turtle.py H:\code.py
```

> Ganti `H:\` dengan drive letter CIRCUITPY di komputer kamu.

CircuitPython memiliki **file watcher** — otomatis mendeteksi perubahan `code.py` dan restart tanpa perlu reset manual.

> ⚠️ **Kalau program tidak jalan otomatis setelah di-copy:**
> Tekan tombol **RESET fisik** di board. Ini terjadi pada program dengan
> tight loop tanpa `time.sleep()` (seperti turtle graphics) — file watcher
> tidak mendapat giliran untuk mendeteksi perubahan file.

---

## Troubleshooting

| Masalah                                                | Solusi                                                       |
| ------------------------------------------------------ | ------------------------------------------------------------ |
| `CIRCUITPY` drive tidak muncul                         | Ganti kabel USB (harus kabel data, bukan charge-only)        |
| `ImportError: no module named 'adafruit_display_text'` | Jalankan `circup install adafruit_display_text` atau copy library dari folder `lib/` |
| `MemoryError` saat import                              | Gunakan CircuitPython 9.2.9 (file .bin disediakan)           |
| Kamera tidak terdeteksi                                | Pastikan firmware mendukung `espcamera` (built-in di 8.2.8+) |
| LCD blank                                              | Board perlu di-reset setelah install library — `mpremote reset` atau cabut-colok USB |
| `mpy` incompatible                                     | Gunakan `circup` (handle versi otomatis), atau gunakan bundle `-py-` untuk copy manual |
