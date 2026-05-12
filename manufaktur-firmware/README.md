# YD-ESP32-S3-EYE (espressif_esp32s3_eye V.2.2) — Manufacturer Firmware

## Pendahuluan

Panduan untuk mengembalikan (flash) firmware bawaan pabrik V2.2 pada board YD-ESP32-S3-EYE. Firmware ini adalah firmware original dari VCC-GND Studio yang menjalankan demo lengkap semua peripheral board (kamera, LCD, WiFi, audio).

Kegunaan: restore board ke kondisi pabrik setelah eksperimen dengan Arduino/CircuitPython.

> **File firmware:** `esp32-s3-eye-v2.2-firmware-v0.2.0-en.bin`

---

## Pin Definition

Tidak relevan — firmware sudah dikonfigurasi untuk board ini. Semua pin mapping sudah built-in di firmware binary.

---

## Library yang Digunakan

| Tool | Fungsi |
|------|--------|
| `esptool` (Python) | Flash tool untuk chip ESP32 |

---

## Cara Instal

### Step 1: Instal esptool

```powershell
pip install esptool
```

### Step 2: Erase Flash (Full Chip Erase)

Colok USB, tekan **BOOT** + **RST** (lepas RST dulu, baru lepas BOOT). Board masuk **Download Mode**.

```powershell
esptool --chip esp32s3 --port COM5 erase-flash
```

**Expected output:**
```
Connecting....
Chip is ESP32-S3
...
Erasing flash (this may take a while)...
Chip erase completed successfully in X.Xs
Hard resetting via RTS pin...
```

### Step 3: Flash Firmware

```powershell
esptool --chip esp32s3 --port COM5 --baud 921600 write-flash -z 0x0 esp32-s3-eye-v2.2-firmware-v0.2.0-en.bin
```

| Parameter | Arti |
|-----------|------|
| `--chip esp32s3` | Target chip ESP32-S3 |
| `--port COM5` | Port serial (sesuaikan) |
| `--baud 921600` | Kecepatan upload |
| `write-flash` | Perintah tulis flash |
| `-z` | Kompresi data |
| `0x0` | Alamat awal flash (offset 0) |

### Step 4: Reset Board

Tekan tombol **RST** saja (tanpa BOOT) untuk boot normal. Board akan menjalankan firmware pabrik.

---

## Alur Berpikir

```
MULAI:
  ├─ Instal esptool (pip install esptool)
  ├─ Masuk Download Mode (BOOT+RST, lepas RST, lepas BOOT)
  ├─ Erase flash (full chip) → bersihkan semua data
  ├─ Flash firmware .bin ke offset 0x0 (921600 baud)
  │   └─ Gagal? → Turunkan baud ke 460800
  ├─ Reset board (RST saja)
  └─ Verifikasi board booting normal
```

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Gagal connecting | Turunkan baud rate ke 460800 |
| Port tidak ditemukan | Cek Device Manager, atau `python -m serial.tools.list_ports` |
| `Chip erase failed` | Pastikan board dalam Download Mode (BOOT+RST) |
| Board tidak booting setelah flash | Tekan RST sekali lagi, tunggu 5 detik |
| `Wrong boot mode detected` | Jangan tekan BOOT saat RST — cukup RST saja untuk boot normal |
