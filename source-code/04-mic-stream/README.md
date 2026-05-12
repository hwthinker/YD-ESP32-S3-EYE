# 04 — Mic Stream + Python Analyzer

Stream audio realtime dari mikrofon ESP32-S3-EYE ke komputer via Serial USB. Python menampilkan waveform, spektrum FFT, volume history, dan info kualitas suara secara realtime.

---

## Hardware — Pin Mikrofon I2S

| Sinyal I2S | GPIO |
|------------|------|
| WS (LRCK)  | 42   |
| SCK (BCK)  | 41   |
| SD (DATA)  | 2    |

---

## Arsitektur

```
ESP32-S3-EYE                    Komputer
┌─────────────────┐             ┌──────────────────────┐
│  I2S Mic        │             │  mic_analyzer.py     │
│  → 16kHz 16-bit │──Serial──▶  │  ┌──────────────┐   │
│  → frame paket  │  921600     │  │  Waveform    │   │
│  [MAGIC][count] │  baud       │  │  FFT Spectrum│   │
│  [PCM data]     │             │  │  RMS History │   │
└─────────────────┘             │  │  Info Panel  │   │
                                │  └──────────────┘   │
                                └──────────────────────┘
```

---

## Instalasi Python

```powershell
cd source-code\04-mic-stream
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

### Step 1 — Upload ke ESP32

1. Buka `04-mic-stream.ino` di Arduino IDE
2. Setting board:

   | Setting       | Nilai                 |
   |---------------|-----------------------|
   | Board         | ESP32S3 Dev Module    |
   | Port          | COM5 (sesuaikan)      |
   | Upload Speed  | 921600                |
   | USB Mode      | Hardware CDC and JTAG |

3. Klik **Upload**
4. **Tutup Serial Monitor** Arduino IDE (penting — tidak boleh dua program buka port bersamaan)

### Step 2 — Jalankan Python

```powershell
python mic_analyzer.py
```

Jendela analyzer akan terbuka. Bicara atau tepuk tangan untuk melihat respons.

---

## Tampilan Panel

```
┌────────────────────────────────────────────────────┐
│  Waveform (1 detik terakhir)                       │
│  Garis hijau = amplitudo suara realtime            │
├────────────────────────────────────────────────────┤
│  Spektrum Frekuensi (FFT)                          │
│  ■ Biru  = Bass 80–300 Hz                          │
│  ■ Hijau = Suara manusia 300–3400 Hz               │
│  ■ Jingga= Treble > 3.4 kHz                        │
├───────────────────┬────────────────────────────────┤
│  Volume History   │  RMS, Peak (dBFS)              │
│  (5 detik)        │  SNR estimate + kualitas       │
│                   │  Frekuensi dominan             │
│                   │  Status: SENYAP/NORMAL/KERAS   │
└───────────────────┴────────────────────────────────┘
```

---

## Interpretasi Hasil

| Indikator       | Nilai Baik          | Keterangan |
|-----------------|---------------------|------------|
| SNR > 25 dB     | Sangat Baik         | Signal jauh di atas noise |
| SNR 15–25 dB    | Baik                | Cukup untuk voice/speech  |
| SNR < 8 dB      | Berisik             | Noise floor terlalu tinggi |
| dBFS ≥ −3       | Terlalu keras       | Risiko clipping |
| Dom. Freq       | 80–3400 Hz          | Rentang suara normal manusia |

---

## Troubleshoot

| Masalah | Solusi |
|---------|--------|
| `ERROR: Gagal buka serial` | Tutup Serial Monitor Arduino IDE |
| Grafik tidak bergerak | Pastikan sketch sudah terupload dan board terhubung |
| Port salah | Ganti `PORT = 'COM5'` di baris awal `mic_analyzer.py` |
