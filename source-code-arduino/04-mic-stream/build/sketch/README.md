#line 1 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\04-mic-stream\\README.md"
# 04 — Mic Stream + Python Analyzer

## Pendahuluan

Program streaming audio realtime dari mikrofon I2S ESP32-S3-EYE ke komputer via Serial USB. Data audio dikirim dalam format paket binary dengan magic byte sync. Di sisi komputer, Python (`mic_analyzer.py`) menerima, mendekode, dan menampilkan:
- **Waveform** time-domain (1 detik)
- **Spektrum FFT** frekuensi dengan kode warna (Bass / Suara manusia / Treble)
- **Volume History** RMS selama 5 detik
- **Info Panel** — RMS, Peak dBFS, SNR estimate, frekuensi dominan, status suara

Tujuan: visualisasi audio realtime untuk analisis kualitas sinyal mikrofon.

---

## Pin Definition

| Sinyal I2S | GPIO | Keterangan |
|------------|------|------------|
| WS (LRCK) | 42 | Word Select |
| SCK (BCK) | 41 | Bit Clock |
| SD (DATA) | 2 | Serial Data Input |

---

## Mekanisme Komunikasi (Serial Protocol)

> **Tidak ada komunikasi LoRa.** Komunikasi menggunakan **Serial USB (UART)** antara ESP32 dan PC.

### Format Paket Data (ESP32 → PC)

```
┌──────────────┬──────────────┬─────────────────────┐
│ MAGIC (4 B)  │ count (2 B)  │ PCM Data (count×2 B)│
│ 0xAA 0x55    │ uint16 LE    │ int16 LE × count     │
│ 0xAA 0x55    │              │                      │
└──────────────┴──────────────┴─────────────────────┘
```

| Field | Ukuran | Deskripsi |
|-------|--------|-----------|
| MAGIC | 4 byte | `0xAA 0x55 0xAA 0x55` — penanda awal frame |
| count | 2 byte | Jumlah sampel dalam frame (uint16, little-endian) |
| data | count×2 byte | PCM 16-bit signed, little-endian |

**Spesifikasi Audio:**
- Sample Rate: 16000 Hz
- Bit Depth: 16-bit signed PCM
- Channel: Mono
- Chunk size: 256 sampel per frame (~16 ms)
- Baud Rate Serial: 921600

### Sinkronisasi di Python

Python reader mencari 4 byte magic secara sequential. Jika ditemukan, baca 2 byte count, lalu baca `count × 2` byte data PCM. Thread serial berjalan paralel dengan GUI matplotlib untuk menghindari blocking.

---

## Cara Kerja Program

### Sisi ESP32 (04-mic-stream.ino)

1. **Inisialisasi** — `Serial.begin(921600)` + I2S driver (mode Master RX, 16kHz, 32-bit).
2. **Loop** — Setiap iterasi:
   - `i2s_read()` membaca 256 sampel 32-bit
   - Konversi 32-bit → 16-bit: `raw32[i] >> 16` (ambil 16 bit teratas dari data MSB-aligned)
   - Kirim frame: MAGIC (4B) + count (2B) + PCM data (count×2B) via `Serial.write()`

### Sisi Python (mic_analyzer.py)

1. **Serial Reader Thread** — Membaca dari COM port, mencari magic byte, mengumpulkan chunk audio ke dalam buffer antrian (queue.Queue).
2. **Main Thread (GUI)** — Matplotlib animation loop:
   - Ambil chunk dari queue
   - Update waveform plot (line hijau, 1 detik rolling window)
   - Hitung FFT dengan Hanning window → plot spektrum dengan kode warna
   - Hitung RMS → update volume history (garis kuning, 5 detik)
   - Hitung Peak dBFS, SNR estimate, dominant frequency
   - Update info panel teks

---

## Alur Berpikir (Logic Flow)

### ESP32
```
SETUP:
  ├─ Serial.begin(921600)
  ├─ i2s_driver_install() + i2s_set_pin()
  └─ i2s_zero_dma_buffer()

LOOP:
  ├─ i2s_read(256 samples)
  │   └─ n=0? → return (skip)
  ├─ FOR i=0..n-1: pcm16[i] = raw32[i] >> 16
  ├─ Serial.write(MAGIC, 4)
  ├─ Serial.write(&count, 2)
  ├─ Serial.write(pcm16, n*2)
  └─ Kembali ke LOOP (no delay → max throughput)
```

### Python
```
START:
  ├─ Buka serial port COM5, 921600
  ├─ Start reader thread → cari MAGIC → kumpulkan chunk
  └─ Start matplotlib animation

ANIMATION LOOP (~30 fps):
  ├─ Ambil chunk dari queue
  ├─ Append ke waveform buffer (1 detik)
  ├─ Update waveform plot
  ├─ FFT dengan Hanning window → update spectrum
  ├─ Hitung RMS → update volume history
  ├─ Hitung SNR = 20*log10(RMS_signal / RMS_noise_floor)
  └─ Update info panel teks
```

---

## Hasil

Tampilan GUI 4-panel:

```
┌────────────────────────────────────────────────────┐
│  Waveform (1 detik terakhir)                       │
│  Garis hijau = amplitudo suara realtime            │
├────────────────────────────────────────────────────┤
│  Spektrum Frekuensi (FFT)                          │
│  Biru  = Bass 80–300 Hz                           │
│  Hijau = Suara manusia 300–3400 Hz                 │
│  Jingga= Treble > 3.4 kHz                          │
├───────────────────┬────────────────────────────────┤
│  Volume History   │  RMS, Peak (dBFS)              │
│  (5 detik)        │  SNR estimate + kualitas       │
│                   │  Frekuensi dominan             │
│                   │  Status: SENYAP/NORMAL/KERAS   │
└───────────────────┴────────────────────────────────┘
```

### Interpretasi SNR

| SNR | Kualitas | Keterangan |
|-----|----------|------------|
| > 25 dB | Sangat Baik | Signal jauh di atas noise |
| 15–25 dB | Baik | Cukup untuk voice/speech |
| 8–15 dB | Cukup | Ada noise tapi masih terbaca |
| < 8 dB | Berisik | Noise floor terlalu tinggi |

---

## Library yang Digunakan

### Arduino (built-in)
| Library | Keterangan |
|---------|------------|
| `driver/i2s.h` | I2S audio driver |

### Python (install via pip)
| Library | Versi | Keterangan |
|---------|-------|------------|
| `pyserial` | ≥ 3.5 | Komunikasi serial COM port |
| `numpy` | ≥ 1.24 | Komputasi numerik (FFT, statistik) |
| `matplotlib` | ≥ 3.7 | Plotting GUI realtime |

---

## Cara Instal Library

### Arduino
Tidak perlu — `driver/i2s.h` built-in di ESP32 Arduino Core.

### Python
```powershell
cd source-code-arduino\04-mic-stream
pip install -r requirements.txt
```

Isi `requirements.txt`:
```
pyserial>=3.5
numpy>=1.24
matplotlib>=3.7
```

---

## Cara Pakai

1. Upload `04-mic-stream.ino` ke ESP32-S3-EYE
2. **Tutup Serial Monitor Arduino IDE** (port harus bebas)
3. Jalankan: `python mic_analyzer.py`
4. Bicara/tepuk tangan — grafik bergerak realtime

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `ERROR: Gagal buka serial` | Tutup Serial Monitor Arduino IDE |
| Grafik tidak bergerak | Pastikan sketch terupload dan board terhubung |
| Port salah | Edit `PORT = 'COM5'` di baris awal `mic_analyzer.py` |
| Grafik patah-patah | Turunkan baud rate di sketch dan Python (misal 460800) |
| `ModuleNotFoundError` | Jalankan `pip install -r requirements.txt` |
