#line 1 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\01-test-sdcard\\README.md"
# 01 — Test SD Card

## Pendahuluan

Program uji coba baca/tulis microSD Card pada YD-ESP32-S3-EYE menggunakan antarmuka SDMMC 1-bit. Program akan menampilkan daftar isi direktori root SD Card, lalu menulis file `hello.txt` sebagai bukti bahwa operasi tulis berhasil.

Tujuan: memvalidasi konektivitas hardware SD Card slot dan kompatibilitas library SD_MMC dengan board ini.

---

## Pin Definition

| Pin SDMMC | GPIO | Keterangan |
|-----------|------|------------|
| CLK       | 39   | SDMMC Clock |
| CMD       | 38   | SDMMC Command |
| D0        | 40   | SDMMC Data 0 (1-bit mode) |

> Board YD-ESP32-S3-EYE hanya mendukung mode SDMMC **1-bit**. Pastikan SD Card diformat **FAT32**.

---

## Cara Kerja Program

1. **Inisialisasi Serial** — `Serial.begin(115200)` untuk output monitoring.
2. **Konfigurasi Pin SDMMC** — `SD_MMC.setPins(39, 38, 40)` menetapkan pin CLK, CMD, D0.
3. **Mount SD Card** — `SD_MMC.begin("/sdcard", true)` dengan parameter `true` = mode 1-bit.
4. **Deteksi tipe kartu** — Membaca `cardType()` dan `cardSize()` untuk menampilkan info kartu (MMC/SDSC/SDHC + kapasitas).
5. **List direktori root** — Fungsi `listDir()` membaca semua file di `/` dan menampilkan nama + ukuran.
6. **Tulis file** — Fungsi `writeFile()` membuat `/hello.txt` berisi teks `"hello from esp32-s3 eye-OK"`.
7. **Selesai** — Program berhenti di `setup()`, `loop()` kosong.

---

## Alur Berpikir (Logic Flow)

```
Start
  │
  ├─ Serial.begin(115200)
  ├─ SD_MMC.setPins(39, 38, 40)
  │   └─ Gagal? → "Pin configuration failed!" → STOP
  ├─ SD_MMC.begin("/sdcard", true)  // 1-bit mode
  │   └─ Gagal? → "Card Mount Failed" → STOP
  ├─ Baca cardType + cardSize → tampilkan info
  ├─ listDir("/") → tampilkan isi direktori root
  ├─ writeFile("/hello.txt", "...") → tulis file
  │   └─ Gagal? → "Write failed"
  └─ "Selesai!" → END
```

---

## Hasil

**Serial Monitor Output (baud 115200):**

```
--- ESP32-S3-EYE SD Card Test ---
SD Card Type: SDHC
SD Card Size: 16384MB
Listing directory: /
  FILE: hello.txt  SIZE: 0
Writing file: /hello.txt
File written

Selesai! Anda bisa mencabut SD card dan mengecek file 'hello.txt' di komputer.
```

File `hello.txt` berisi teks `hello from esp32-s3 eye-OK` dan dapat dibuka di komputer setelah SD Card dicabut.

---

## Library yang Digunakan

| Library | Sumber | Keterangan |
|---------|--------|------------|
| `FS.h` | Built-in ESP32 Arduino Core | Filesystem abstraction |
| `SD_MMC.h` | Built-in ESP32 Arduino Core | SDMMC driver 1-bit/4-bit |

> Tidak perlu install library tambahan — kedua library sudah termasuk dalam ESP32 Arduino Core.

---

## Cara Instal Library

Tidak diperlukan instalasi library tambahan. Library `FS.h` dan `SD_MMC.h` sudah built-in di ESP32 Arduino Core (versi 2.x ke atas).

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `Card Mount Failed` | SD Card belum terpasang atau bukan FAT32 |
| `Pin configuration failed` | Versi library SD_MMC tidak mendukung `setPins()` — update ESP32 Arduino Core |
| Tidak terdeteksi | Format ulang SD Card ke FAT32 (bukan exFAT) |
| File tidak terbaca di PC | Cabut SD Card dari board dulu, baru colok ke PC |
