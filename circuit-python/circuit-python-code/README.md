# CircuitPython Scripts for YD-ESP32-S3-EYE

## Pendahuluan

Kumpulan script CircuitPython untuk menguji dan mendemonstrasikan kemampuan YD-ESP32-S3-EYE menggunakan CircuitPython 8.2.8. Mencakup uji coba LCD (warna + turtle graphics) dan kamera OV2640 via modul `espcamera`.

> **Firmware:** `adafruit-circuitpython-espressif_esp32s3_eye-en_US-8.2.8.bin` (tersedia di folder `../circuitpython-firmware/`)

---

## Pin Definition

Board YD-ESP32-S3-EYE menggunakan pin definition bawaan CircuitPython (`board.DISPLAY` dll). Pin mapping otomatis ditangani oleh firmware CircuitPython untuk board `espressif_esp32s3_eye`.

| Peripheral | Interface | Keterangan |
|------------|-----------|------------|
| LCD ST7789V | SPI via displayio | `board.DISPLAY` — 240×240, rotasi otomatis |
| Kamera OV2640 | espcamera | Modul built-in CircuitPython |
| Backlight | GPIO 48 | Dikelola otomatis oleh `board.DISPLAY` |

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

### 5. 05-cpyS3EYE_accelerometer.py — QMA7981/QMA6100P IMU Test

1. Inisialisasi I2C (`busio.I2C`) pada pin SDA=4, SCL=5.
2. Membaca Chip ID dan mengonfigurasi sensor via register I2C.
3. Looping pembacaan nilai raw akselerometer X, Y, Z.
4. Mengkonversi nilai raw (14-bit signed) menjadi skala gravitasi (g).
5. Menampilkan hasil `(ax, ay, az)` ke terminal serial.

### 6. 06-cpyS3EYE_imu_cube.py — 3D Wireframe Cube via IMU

1. Setup LCD (`board.DISPLAY`) dengan `displayio.Bitmap` dan `Palette` 2 warna (hitam, cyan).
2. Membaca data akselerometer IMU (seperti script #5).
3. Menggunakan *low-pass filter* untuk menstabilkan sinyal.
4. Mengkalkulasi *roll* dan *pitch* dari vektor gravitasi.
5. Memproyeksikan verteks kubus 3D ke layar 2D berdasarkan kalkulasi sudut, dan menggambar garis penyambung verteks (*edges*) menggunakan fungsi cepat `bitmaptools.draw_line`.
6. Tampilan di LCD merespons pergerakan orientasi board secara real-time.

### 7. 07-cpyS3EYE_imu_cube_color.py — Colored 3D Cube

1. Modifikasi dari `06-cpyS3EYE_imu_cube.py`.
2. Menggunakan palet 4 warna (Hitam, Merah, Hijau, Biru Terang).
3. Mewarnai sisi-sisi kubus berdasarkan sumbunya untuk mempermudah identifikasi orientasi saat board digerakkan:
   - Sumbu X: Merah
   - Sumbu Y: Hijau
   - Sumbu Z: Biru Terang



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

### QMA7981/QMA6100P Accelerometer
Menampilkan log orientasi gravitasi sumbu X, Y, Z di terminal secara berkelanjutan.

### 3D Wireframe Cube (Monochrome / Color)
LCD menampilkan kubus 3D yang berputar secara responsif mengikuti kemiringan (tilt) dari YD-ESP32-S3-EYE berkat integrasi IMU dan LCD. Pada versi "color", kubus memiliki garis berwarna sesuai standar orientasi sumbu (RGB untuk XYZ) sehingga orientasi 3D-nya sangat intuitif.

> **Catatan:** Fitur Microphone I2S (MSM261S4030H0) tidak didukung dalam lingkungan CircuitPython pada versi firmware 8.x/9.x saat ini (modul `audiobusio.I2SIn` tidak dikompilasi). Untuk proyek yang membutuhkan mic bawaan, direkomendasikan untuk menggunakan framework Arduino (folder `source-code-arduino`).



## Library yang Digunakan

### CircuitPython (ada di bundle Adafruit)

| Library | Fungsi | Digunakan oleh |
|---------|--------|----------------|
| `adafruit_display_text` | Label teks di LCD | `cpyS3EYE_LCD_color.py` |
| `adafruit_bitmap_font` | Dependency display_text | (otomatis) |
| `adafruit_turtle` | Turtle graphics untuk displayio | `cpyS3EYE_turtle.py` |
| `adafruit_espcamera` | Driver kamera OV2640 | `cpS3EYE_espcamera_displayio.py` |



## Cara Instal Library

> **PENTING:** Selalu gunakan bundle `-py-` (source code Python), **bukan** `-mpy-` (terkompilasi). File `.mpy` harus kompatibel dengan versi CircuitPython yang persis sama.

### Langkah 1: Download Bundle

Download dari: https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases

Cari file dengan nama: `adafruit-circuitpython-bundle-py-20xxxxxx.zip`

> Bundle offline juga tersedia di `../circuitpython-firmware/circuitpython-community-bundle-8.x-mpy-*.zip`

### Langkah 2: Copy ke CIRCUITPY

1. Colok ESP32-S3-EYE via USB-C → drive `CIRCUITPY` muncul
2. Extract bundle, buka folder `lib/`
3. Copy folder library yang diperlukan ke `CIRCUITPY/lib/`

**Untuk LCD Color Test:**
```
copy: adafruit-circuitpython-bundle-py-xxx\lib\adafruit_display_text\  →  CIRCUITPY\lib\adafruit_display_text\
copy: adafruit-circuitpython-bundle-py-xxx\lib\adafruit_bitmap_font\   →  CIRCUITPY\lib\adafruit_bitmap_font\
```

**Untuk Turtle Graphics:**
```
copy: adafruit-circuitpython-bundle-py-xxx\lib\adafruit_turtle.py  →  CIRCUITPY\lib\adafruit_turtle.py
```

### Langkah 3: Jalankan Script

```powershell
# Via mpremote (recommended)
mpremote run cpyS3EYE_LCD_color.py

# Atau copy ke code.py untuk auto-run
copy cpyS3EYE_LCD_color.py H:\code.py
```

### Backup Offline (dari folder lib/)

Folder `lib/` di direktori ini berisi backup library:
```
lib/
├── adafruit_bitmap_font/
├── adafruit_display_text/
└── adafruit_turtle.py
```

Gunakan jika tidak ada internet:
```powershell
xcopy lib\* H:\lib\ /E /Y
```

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `CIRCUITPY` drive tidak muncul | Ganti kabel USB (harus kabel data, bukan charge-only) |
| `ImportError: no module named 'adafruit_display_text'` | Library belum di-copy ke `CIRCUITPY/lib/` |
| `MemoryError` saat import | Gunakan CircuitPython 8.2.8 (file .bin disediakan) |
| Kamera tidak terdeteksi | Pastikan firmware mendukung `espcamera` (built-in di 8.2.8+) |
| LCD blank | Board perlu di-reset setelah copy library — tekan RST atau cabut-colok USB |
| `mpy` incompatible | Bundle `.mpy` harus cocok dengan versi CircuitPython — selalu gunakan bundle `-py-` |
