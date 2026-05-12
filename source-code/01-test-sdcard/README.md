# 01 — Test SD Card

Test baca/tulis microSD Card pada ESP32-S3-EYE menggunakan antarmuka SDMMC 1-bit.

---

## Hardware

| Pin SDMMC | GPIO |
|-----------|------|
| CLK       | 39   |
| CMD       | 38   |
| D0        | 40   |

Pastikan SD Card sudah diformat **FAT32** dan terpasang di slot board.

---

## Arduino IDE Settings

| Setting            | Nilai                  |
|--------------------|------------------------|
| Board              | ESP32S3 Dev Module     |
| Port               | COM5 (sesuaikan)       |
| Upload Speed       | 921600                 |
| USB Mode           | Hardware CDC and JTAG  |

> Lihat screenshot lengkap di [`../../assets/image-20260511042139739.png`](../../assets/image-20260511042139739.png)

---

## Cara Upload

1. Pasang SD Card ke slot board
2. Buka `01-test-sdcard.ino` di Arduino IDE
3. Pilih board dan port yang sesuai
4. Klik **Upload**
5. Buka **Serial Monitor** → baud **115200**

---

## Expected Output

```
--- ESP32-S3-EYE SD Card Test ---
Listing directory: /
  FILE: hello.txt  SIZE: 0
Writing file: /hello.txt
File written

Selesai! Anda bisa mencabut SD card dan mengecek file 'hello.txt' di komputer.
```

File `hello.txt` berisi teks `hello from esp32-s3 eye-OK` dan bisa dibuka di komputer setelah SD Card dicabut.

---

## Troubleshoot

| Masalah | Solusi |
|---------|--------|
| `Card Mount Failed` | SD Card belum terpasang atau bukan FAT32 |
| `Pin configuration failed` | Versi library SD_MMC tidak mendukung `setPins()` — update ESP32 Arduino Core |
| Tidak terdeteksi | Coba format ulang SD Card ke FAT32 (bukan exFAT) |
