# 05 — Mic Record & Playback

Rekam audio dari mikrofon ESP32-S3-EYE, tampilkan realtime di komputer, simpan ke file WAV, dan putar kembali — semua dari satu GUI Python.

File WAV yang dihasilkan bisa dibuka di VLC, Windows Media Player, Audacity, atau media player apapun.

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
┌─────────────────┐             ┌──────────────────────────────┐
│  I2S Mic        │             │  mic_recorder.py             │
│  → 16kHz 16-bit │──Serial──▶  │  ┌────────────────────────┐ │
│  PCM stream     │  921600     │  │ Waveform + FFT + History│ │
└─────────────────┘  baud       │  ├────────────────────────┤ │
                                │  │ [● REC] [■ STOP]       │ │
                                │  │ [▶ PLAY] [📁 OPEN]     │ │
                                │  └────────────────────────┘ │
                                │  recordings/rec_*.wav ──▶ 💾 │
                                └──────────────────────────────┘
```

---

## Instalasi Python

```powershell
cd source-code\05-mic-record
pip install -r requirements.txt
```

Isi `requirements.txt`:
```
pyserial>=3.5
numpy>=1.24
matplotlib>=3.7
sounddevice>=0.4
```

---

## Cara Pakai

### Step 1 — Upload ke ESP32

1. Buka `05-mic-record.ino` di Arduino IDE
2. Setting board:

   | Setting       | Nilai                 |
   |---------------|-----------------------|
   | Board         | ESP32S3 Dev Module    |
   | Port          | COM5 (sesuaikan)      |
   | Upload Speed  | 921600                |
   | USB Mode      | Hardware CDC and JTAG |

3. Klik **Upload**
4. **Tutup Serial Monitor** Arduino IDE

### Step 2 — Jalankan Python

```powershell
python mic_recorder.py
```

---

## Tampilan GUI

```
┌────────────────────────────────────────────────────────┐
│  ESP32-S3-EYE  ─  Mic Recorder & Analyzer             │
├────────────────────────────────────────────────────────┤
│  Waveform (1 detik)   ● berkedip merah saat MEREKAM   │
├────────────────────────────────────────────────────────┤
│  Spektrum Frekuensi (FFT)                              │
│  ■ Biru = Bass  ■ Hijau = Suara  ■ Jingga = Treble    │
├─────────────────────┬──────────────────────────────────┤
│  Volume History (5s)│  RMS, Peak, SNR, Dom. Freq       │
│  (garis kuning)     │  Status + nama file terakhir     │
├─────────────────────┴──────────────────────────────────┤
│  [● REC]  [■ STOP]  [▶ PLAY]  [📁 OPEN]               │
│  ─ status: Tersimpan: rec_20260511_060555.wav (3.2s) ─ │
└────────────────────────────────────────────────────────┘
```

---

## Tombol & Keyboard Shortcut

| Tombol GUI  | Keyboard | Fungsi                                    |
|-------------|----------|-------------------------------------------|
| **● REC**   | `R`      | Mulai merekam audio                       |
| **■ STOP**  | `S`      | Stop rekaman, simpan ke file WAV          |
| **▶ PLAY**  | `P`      | Putar rekaman terakhir lewat speaker      |
| **📁 OPEN** | —        | Buka folder `recordings/` di Explorer    |

---

## Alur Penggunaan Tipikal

```
1. Jalankan Python → GUI terbuka
2. Tekan R  (atau klik REC)   → judul berubah "● MEREKAM 0.0s"
3. Bicara / nyanyi / tepuk tangan
4. Tekan S  (atau klik STOP)  → status bar: "Tersimpan: rec_xxx.wav (3.2s)"
5. Tekan P  (atau klik PLAY)  → suara terdengar di speaker komputer
6. Klik OPEN → buka Explorer, file WAV siap dibuka di media player
```

---

## File Output

| Item | Detail |
|------|--------|
| Format  | WAV (PCM 16-bit, mono)       |
| Sample Rate | 16.000 Hz               |
| Lokasi  | `recordings/rec_YYYYMMDD_HHMMSS.wav` |
| Kompatibel | VLC, Windows Media Player, Audacity, dsb. |

---

## Troubleshoot

| Masalah | Solusi |
|---------|--------|
| `ERROR serial` | Tutup Serial Monitor Arduino IDE, pastikan port COM5 benar |
| Tidak ada suara saat PLAY | Cek volume speaker komputer, coba install ulang `sounddevice` |
| File WAV kosong / pendek | Pastikan REC sudah aktif (judul berkedip) sebelum bicara |
| Port salah | Edit baris `PORT = 'COM5'` di `mic_recorder.py` |
