#line 1 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\03-test-mic\\README.md"
# 03 — Test Mic (Serial Monitor)

## Pendahuluan

Program monitoring mikrofon I2S digital MSM261S4030H0 pada YD-ESP32-S3-EYE secara realtime. Output ditampilkan sebagai bar graph ASCII di Serial Monitor lengkap dengan nilai RMS, Peak, dan label status suara (SENYAP / normal / KERAS / SANGAT KERAS).

Tujuan: memvalidasi fungsi mikrofon I2S dan mengkalibrasi threshold level suara untuk board ini.

---

## Pin Definition

| Sinyal I2S | GPIO | Keterangan |
|------------|------|------------|
| WS (LRCK) | 42 | Word Select — clock pemisah channel kiri/kanan |
| SCK (BCK) | 41 | Bit Clock — clock data serial |
| SD (DATA) | 2 | Serial Data Input dari mikrofon |

**Konfigurasi I2S:**
- Port: `I2S_NUM_0`
- Sample Rate: 16000 Hz
- Bits per sample: 32-bit (I2S standard)
- Channel: Left only (mono)
- DMA buffer: 4 buffer × 512 samples

---

## Cara Kerja Program

1. **Inisialisasi I2S Driver** — `i2s_driver_install()` + `i2s_set_pin()` mengkonfigurasi hardware I2S dalam mode Master RX.
2. **Flush buffer awal** — `i2s_zero_dma_buffer()` membuang sampel pertama yang sering mengandung noise.
3. **Loop monitoring** — Setiap ~80ms:
   - `i2s_read()` membaca 512 sampel 32-bit dari DMA buffer
   - **Normalisasi**: Setiap sampel digeser kanan 14 bit (`>> 14`) untuk membuang noise LSB, menyisakan 18 bit atas yang valid (MSM261S4030H0 adalah mic 18-bit efektif dalam format 32-bit I2S)
   - **RMS**: Akar kuadrat dari rata-rata kuadrat sampel — merepresentasikan energi suara
   - **Peak**: Nilai absolut tertinggi dalam buffer
   - **Bar Graph**: Visualisasi 40 karakter dengan gradasi karakter (`.` rendah, `:` sedang, `|` keras, `#` puncak)
   - **Status**: Label berdasarkan threshold RMS

---

## Alur Berpikir (Logic Flow)

```
SETUP:
  ├─ Serial.begin(115200)
  ├─ i2s_driver_install(I2S_NUM_0, config)
  │   └─ Gagal? → ERROR → STOP
  ├─ i2s_set_pin(I2S_NUM_0, pins)
  ├─ i2s_zero_dma_buffer() → flush noise
  └─ Tampilkan header monitoring

LOOP:
  ├─ i2s_read(512 samples, timeout 200ms)
  │   └─ No data? → WARN → delay(300)
  ├─ Hitung RMS: sqrt(Σ(s >> 14)² / n)
  ├─ Hitung Peak: max(|s >> 14|)
  ├─ Cetak baris: RMS | Peak | Bar Graph | Status
  │   ├─ printBar(): map RMS ke 40 karakter
  │   │   ├─ 0–40%  → ':'
  │   │   ├─ 40–70% → '|'
  │   │   └─ 70–100%→ '#'
  │   └─ printStatus():
  │       ├─ RMS < 60     → "SENYAP"
  │       ├─ RMS < 400    → "normal"
  │       ├─ RMS < 1500   → "KERAS"
  │       └─ RMS ≥ 1500   → "SANGAT KERAS"
  └─ delay(80) → ~12 update/detik
```

---

## Hasil

**Serial Monitor Output (baud 115200):**

```
╔════════════════════════════════════════════╗
║  ESP32-S3-EYE  ─  MIC TEST & MONITOR      ║
╚════════════════════════════════════════════╝

  Mic pins  : WS=42  SCK=41  DATA=2
  Sample rate: 16000 Hz

Inisialisasi I2S driver...
  [OK] Mikrofon siap!

  Bicara atau tepuk tangan dekat board...

  RMS    Peak   | Bar (0──────────max) | Status
  ─────────────────────────────────────────────
     34      78  |........................................|  [  SENYAP  ]
    340    1200  |::::::::::|.............................|  [  normal  ]
   1800    6500  |:::::::::::::::||||#####.............|  [  KERAS   ]
   2741   19128  |::::::::::::::::||||||||||||###.......|  [!!SANGAT KERAS!!]
```

### Threshold Kalibrasi

| Status | RMS Range | Keterangan |
|--------|-----------|------------|
| SENYAP | < 60 | Noise floor board ~30–60 RMS |
| normal | 60 – 400 | Bicara normal |
| KERAS | 400 – 1500 | Bicara keras / tepuk tangan |
| SANGAT KERAS | > 1500 | Tepuk sangat keras / dekat mic |

---

## Library yang Digunakan

| Library | Sumber | Keterangan |
|---------|--------|------------|
| `driver/i2s.h` | Built-in ESP32 Arduino Core | I2S driver untuk audio input/output |

> Tidak perlu install library tambahan.

---

## Cara Instal Library

Tidak diperlukan — `driver/i2s.h` sudah termasuk dalam ESP32 Arduino Core.

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| RMS selalu 0 | Cek koneksi pin WS/SCK/DATA — pastikan sesuai (42, 41, 2) |
| Error install I2S driver | Library lain sudah memakai `I2S_NUM_0` — ganti ke `I2S_NUM_1` |
| RMS sangat tinggi tanpa suara | Ubah shift `>> 14` menjadi `>> 12` atau `>> 16` di baris normalisasi |
| Tidak ada output di Serial Monitor | Pastikan baud rate 115200 |
