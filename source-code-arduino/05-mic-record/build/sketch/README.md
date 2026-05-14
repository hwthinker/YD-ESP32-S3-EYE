#line 1 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\05-mic-record\\README.md"
# 05 — Mic Record & Playback

## Pendahuluan

Program perekam audio lengkap dari mikrofon ESP32-S3-EYE. Data audio di-stream ke komputer via Serial USB, ditampilkan secara realtime (waveform + FFT), dapat direkam ke file WAV, dan diputar kembali melalui speaker komputer — semua dari satu GUI Python.

File WAV yang dihasilkan kompatibel dengan VLC, Windows Media Player, Audacity, dan media player lainnya.

Tujuan: solusi all-in-one untuk merekam, menganalisis, dan memutar ulang audio dari mikrofon ESP32-S3-EYE.

---

## Pin Definition

| Sinyal I2S | GPIO | Keterangan |
|------------|------|------------|
| WS (LRCK) | 42 | Word Select |
| SCK (BCK) | 41 | Bit Clock |
| SD (DATA) | 2 | Serial Data Input |

---

## Mekanisme Komunikasi (Serial Protocol)

> **Tidak ada komunikasi LoRa.** Komunikasi menggunakan **Serial USB (UART)** — protokol identik dengan 04-mic-stream.

### Format Paket Data

```
┌──────────────┬──────────────┬─────────────────────┐
│ MAGIC (4 B)  │ count (2 B)  │ PCM Data (count×2 B)│
│ 0xAA 0x55    │ uint16 LE    │ int16 LE × count     │
│ 0xAA 0x55    │              │                      │
└──────────────┴──────────────┴─────────────────────┘
```

- Sample Rate: 16000 Hz, 16-bit PCM, Mono
- Baud Rate: 921600
- Chunk: 256 sampel per frame (~16 ms)

Python reader mencari magic byte, lalu mengumpulkan chunk audio. Saat mode REC aktif, semua data yang masuk disimpan ke buffer. Saat STOP ditekan, buffer dikonversi dan disimpan sebagai file WAV.

---

## Cara Kerja Program

### Sisi ESP32 (05-mic-record.ino)
Identik dengan 04-mic-stream.ino — stream audio I2S via Serial.

### Sisi Python (mic_recorder.py)

1. **Serial Reader Thread** — Membaca data audio dari COM port, memasukkan ke queue.
2. **GUI Main Thread**:
   - **Panel Atas**: Waveform + FFT Spectrum + Volume History + Info (sama seperti mic_analyzer)
   - **Panel Bawah**: 4 tombol kontrol (REC, STOP, PLAY, OPEN)
   - **Status Bar**: Menampilkan status recording, durasi, dan nama file terakhir
3. **Mode Recording**:
   - Tombol REC / keyboard `R` → mulai merekam ke buffer (`recording_buffer`)
   - Indikator ● merah berkedip di judul window
   - Tombol STOP / keyboard `S` → hentikan, simpan buffer sebagai file WAV
4. **Mode Playback**:
   - Tombol PLAY / keyboard `P` → putar file WAV terakhir via `sounddevice`
5. **Output File**:
   - Format: WAV PCM 16-bit, mono, 16000 Hz
   - Nama: `recordings/rec_YYYYMMDD_HHMMSS.wav`
   - Folder `recordings/` dibuat otomatis jika belum ada

---

## Alur Berpikir (Logic Flow)

```
START:
  ├─ Buka serial COM5, 921600
  ├─ Start reader thread
  └─ Start matplotlib GUI

GUI EVENT LOOP:
  ├─ Data audio masuk dari queue
  │   ├─ Update waveform plot (rolling 1 detik)
  │   ├─ Update FFT spectrum (Hanning window)
  │   └─ Update volume history (5 detik)
  │
  ├─ Jika mode REC aktif:
  │   └─ Append data ke recording_buffer
  │
  ├─ Tombol REC (R):
  │   └─ recording_buffer.clear() → mode REC = ON → judul berkedip
  │
  ├─ Tombol STOP (S):
  │   └─ Jika mode REC ON:
  │       ├─ Konversi buffer → array numpy int16
  │       ├─ Simpan WAV: rec_YYYYMMDD_HHMMSS.wav
  │       └─ mode REC = OFF → update status bar
  │
  ├─ Tombol PLAY (P):
  │   └─ Jika ada file terakhir:
  │       ├─ Baca WAV dengan scipy.io.wavfile
  │       └─ sounddevice.play() → putar via speaker
  │
  └─ Tombol OPEN:
      └─ Buka folder recordings/ di Explorer
```

---

## Hasil

### Tampilan GUI

```
┌────────────────────────────────────────────────────────┐
│  ● MEREKAM 3.2s  —  ESP32-S3-EYE Mic Recorder         │
├────────────────────────────────────────────────────────┤
│  Waveform (1 detik)                                    │
├────────────────────────────────────────────────────────┤
│  Spektrum Frekuensi (FFT)                              │
│  Biru = Bass  Hijau = Suara  Jingga = Treble          │
├─────────────────────┬──────────────────────────────────┤
│  Volume History (5s)│  RMS, Peak, SNR, Dom. Freq       │
├─────────────────────┴──────────────────────────────────┤
│  [● REC]  [■ STOP]  [▶ PLAY]  [📁 OPEN]               │
│  ─ Tersimpan: rec_20260511_060555.wav (3.2s) ─        │
└────────────────────────────────────────────────────────┘
```

### File Output WAV

| Properti | Nilai |
|----------|-------|
| Format | WAV (PCM 16-bit, mono) |
| Sample Rate | 16000 Hz |
| Lokasi | `recordings/rec_YYYYMMDD_HHMMSS.wav` |
| Kompatibel | VLC, Windows Media Player, Audacity |

---

## Library yang Digunakan

### Arduino (built-in)
| Library | Keterangan |
|---------|------------|
| `driver/i2s.h` | I2S audio driver |

### Python (install via pip)
| Library | Versi | Keterangan |
|---------|-------|------------|
| `pyserial` | ≥ 3.5 | Komunikasi serial |
| `numpy` | ≥ 1.24 | Komputasi numerik |
| `matplotlib` | ≥ 3.7 | GUI plotting |
| `sounddevice` | ≥ 0.4 | Audio playback |

---

## Cara Instal Library

```powershell
cd source-code-arduino\05-mic-record
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

1. Upload `05-mic-record.ino` ke ESP32
2. **Tutup Serial Monitor** Arduino IDE
3. Jalankan Python: `python mic_recorder.py`
4. GUI terbuka → tekan `R` untuk merekam, `S` untuk stop & simpan, `P` untuk playback

### Shortcut Keyboard

| Tombol | Keyboard | Fungsi |
|--------|----------|--------|
| ● REC | `R` | Mulai merekam |
| ■ STOP | `S` | Stop & simpan WAV |
| ▶ PLAY | `P` | Putar rekaman terakhir |
| 📁 OPEN | — | Buka folder recordings |

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `ERROR serial` | Tutup Serial Monitor Arduino IDE, pastikan COM5 benar |
| Tidak ada suara saat PLAY | Cek volume speaker, install ulang `sounddevice` |
| File WAV kosong/pendek | Pastikan mode REC sudah aktif (judul berkedip) sebelum bicara |
| Port salah | Edit `PORT = 'COM5'` di `mic_recorder.py` |
| `ModuleNotFoundError: sounddevice` | `pip install sounddevice` |
