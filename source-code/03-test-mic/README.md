# 03 — Test Mic (Serial Monitor)

Test dan monitoring mikrofon I2S digital (MSM261S4030H0) pada ESP32-S3-EYE. Output ditampilkan langsung di Serial Monitor Arduino IDE sebagai bar graph ASCII.

---

## Hardware — Pin Mikrofon I2S

| Sinyal I2S | GPIO | Keterangan          |
|------------|------|---------------------|
| WS (LRCK)  | 42   | Word Select         |
| SCK (BCK)  | 41   | Bit Clock           |
| SD (DATA)  | 2    | Serial Data Input   |

---

## Arduino IDE Settings

| Setting            | Nilai                  |
|--------------------|------------------------|
| Board              | ESP32S3 Dev Module     |
| Port               | COM5 (sesuaikan)       |
| Upload Speed       | 921600                 |
| USB Mode           | Hardware CDC and JTAG  |

---

## Cara Upload

1. Buka `03-test-mic.ino` di Arduino IDE
2. Pilih board dan port
3. Klik **Upload**
4. Buka **Serial Monitor** → baud **115200**

---

## Cara Pakai

Setelah Serial Monitor terbuka, langsung bicara atau tepuk tangan dekat board. Bar graph akan bergerak sesuai level suara.

---

## Format Output

```
  RMS    Peak   | Bar (0──────────max) | Status
  ─────────────────────────────────────────────
     34      78  |........................................|  [  SENYAP  ]
    340    1200  |::::::::::|.............................|  [  normal  ]
   1800    6500  |:::::::::::::::||||#####.............|  [  KERAS   ]
   2741   19128  |::::::::::::::::||||||||||||###.......|  [!!SANGAT KERAS!!]
```

### Kolom Output

| Kolom  | Keterangan |
|--------|------------|
| RMS    | Root Mean Square — rata-rata energi suara |
| Peak   | Nilai sampel tertinggi (absolut) |
| Bar    | Visualisasi level: `:` rendah, `\|` sedang, `#` tinggi |
| Status | Label kondisi suara |

### Threshold

| Status         | RMS         |
|----------------|-------------|
| SENYAP         | < 60        |
| normal         | 60 – 400    |
| KERAS          | 400 – 1500  |
| SANGAT KERAS   | > 1500      |

> Nilai kalibrasi dari pengujian nyata pada board ini. Noise floor board ~30–60 RMS saat senyap.

---

## Troubleshoot

| Masalah | Solusi |
|---------|--------|
| RMS selalu 0 | Cek pin WS/SCK/DATA — pastikan sesuai |
| Error install I2S driver | Library lain sudah memakai `I2S_NUM_0` |
| RMS sangat tinggi tanpa suara | Coba ubah `>> 14` menjadi `>> 12` atau `>> 16` di baris normalisasi |
