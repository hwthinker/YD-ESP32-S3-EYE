"""
mic_analyzer.py
Realtime audio quality analyzer untuk ESP32-S3-EYE mic stream.

Cara pakai:
  1. Upload 04-mic-stream.ino ke board, TUTUP Serial Monitor Arduino IDE
  2. pip install -r requirements.txt
  3. python mic_analyzer.py

Panel yang ditampilkan:
  - Waveform  : bentuk gelombang 1 detik terakhir
  - Spektrum  : frekuensi (FFT) dalam dBFS
  - History   : riwayat volume RMS 5 detik terakhir
  - Info      : RMS, Peak, SNR, frekuensi dominan, status kualitas
"""

import serial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec
import struct
import threading
import collections

# ── Konfigurasi ──────────────────────────────────────────
PORT        = 'COM5'
BAUD        = 921600
SAMPLE_RATE = 16000          # Hz, harus sama dengan sketch
MAGIC       = b'\xaa\x55\xaa\x55'

WAVEFORM_SEC  = 1.0          # durasi waveform yang ditampilkan
HISTORY_SEC   = 5.0          # durasi history RMS
FFT_SIZE      = 2048         # resolusi FFT (lebih besar = lebih detail)

WAVE_N    = int(SAMPLE_RATE * WAVEFORM_SEC)
HIST_N    = 200              # titik-titik di history plot

# ── Buffer thread-safe ────────────────────────────────────
waveform_buf = np.zeros(WAVE_N, dtype=np.float32)
rms_history  = collections.deque(np.zeros(HIST_N), maxlen=HIST_N)
buf_lock     = threading.Lock()
connected    = threading.Event()

# ── Serial reader (thread terpisah) ──────────────────────
def serial_reader():
    global waveform_buf
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        connected.set()
        print(f"[OK] Terhubung ke {PORT} @ {BAUD} baud")
    except serial.SerialException as e:
        print(f"[ERROR] Gagal buka serial: {e}")
        print(f"  → Pastikan COM5 benar dan Arduino IDE Serial Monitor sudah ditutup")
        return

    raw = bytearray()
    while True:
        try:
            chunk = ser.read(ser.in_waiting or 256)
        except Exception:
            break
        if not chunk:
            continue
        raw.extend(chunk)

        # Proses semua frame lengkap dalam buffer
        while True:
            idx = raw.find(MAGIC)
            if idx == -1:
                # Tidak ada magic → buang semua kecuali 3 byte terakhir
                if len(raw) > 3:
                    raw = bytearray(raw[-3:])
                break
            if idx > 0:
                raw = raw[idx:]       # buang data sebelum magic

            # Butuh minimal 4 (magic) + 2 (count) = 6 byte header
            if len(raw) < 6:
                break

            count     = struct.unpack_from('<H', raw, 4)[0]
            frame_len = 4 + 2 + count * 2

            if len(raw) < frame_len:
                break                 # tunggu data lebih banyak

            # Ekstrak samples
            data_bytes = raw[6:6 + count * 2]
            raw        = raw[frame_len:]

            samples = (np.frombuffer(data_bytes, dtype='<i2').astype(np.float32)
                       / 32768.0)

            with buf_lock:
                waveform_buf = np.roll(waveform_buf, -len(samples))
                waveform_buf[-len(samples):] = samples
                rms_val = float(np.sqrt(np.mean(samples ** 2)))
                rms_history.append(rms_val)

reader_thread = threading.Thread(target=serial_reader, daemon=True)
reader_thread.start()

# ── Setup matplotlib ──────────────────────────────────────
plt.rcParams['toolbar'] = 'None'
fig = plt.figure(figsize=(14, 9), facecolor='#0d0d1a')
fig.canvas.manager.set_window_title('ESP32-S3-EYE – Mic Analyzer')

gs = GridSpec(3, 2, figure=fig,
              hspace=0.50, wspace=0.30,
              left=0.07, right=0.97, top=0.93, bottom=0.07)

ax_wave = fig.add_subplot(gs[0, :])
ax_fft  = fig.add_subplot(gs[1, :])
ax_hist = fig.add_subplot(gs[2, 0])
ax_info = fig.add_subplot(gs[2, 1])

BG = '#111128'
for ax in [ax_wave, ax_fft, ax_hist, ax_info]:
    ax.set_facecolor(BG)
    ax.tick_params(colors='#9090bb')
    for spine in ax.spines.values():
        spine.set_color('#2a2a5a')

# ── Waveform ─────────────────────────────────────────────
t_axis = np.linspace(0, WAVEFORM_SEC, WAVE_N)
line_wave, = ax_wave.plot(t_axis, np.zeros(WAVE_N), color='#00e676', lw=0.7)
ax_wave.set_xlim(0, WAVEFORM_SEC)
ax_wave.set_ylim(-1, 1)
ax_wave.set_title('Waveform  (1 detik terakhir)', color='#ccccff', pad=5, fontsize=11)
ax_wave.set_xlabel('Waktu (s)', color='#7070aa', fontsize=9)
ax_wave.set_ylabel('Amplitude', color='#7070aa', fontsize=9)
ax_wave.axhline(0, color='#2a2a5a', lw=0.8)
ax_wave.grid(True, color='#1a1a3a', lw=0.5)

# ── FFT Spectrum ─────────────────────────────────────────
freqs   = np.fft.rfftfreq(FFT_SIZE, 1 / SAMPLE_RATE)
line_fft, = ax_fft.plot(freqs, np.full(len(freqs), -80.0), color='#ff6b6b', lw=0.9)
ax_fft.set_xlim(0, SAMPLE_RATE / 2)
ax_fft.set_ylim(-80, 0)
ax_fft.set_title('Spektrum Frekuensi (FFT)', color='#ccccff', pad=5, fontsize=11)
ax_fft.set_xlabel('Frekuensi (Hz)', color='#7070aa', fontsize=9)
ax_fft.set_ylabel('Level (dBFS)', color='#7070aa', fontsize=9)
ax_fft.grid(True, color='#1a1a3a', lw=0.5)
# Highlight rentang suara manusia
ax_fft.axvspan(80,   300,  alpha=0.06, color='#4466ff', label='Bass (80–300Hz)')
ax_fft.axvspan(300,  3400, alpha=0.08, color='#44ff88', label='Suara (300–3400Hz)')
ax_fft.axvspan(3400, 8000, alpha=0.04, color='#ffaa44', label='Treble (>3.4kHz)')
ax_fft.legend(loc='upper right', fontsize=7, facecolor='#111128',
              labelcolor='#aaaacc', framealpha=0.8)

# ── RMS History ───────────────────────────────────────────
h_axis = np.linspace(-HISTORY_SEC, 0, HIST_N)
hist_fill = ax_hist.fill_between(h_axis, 0, np.zeros(HIST_N),
                                  alpha=0.35, color='#ffeb3b')
line_hist, = ax_hist.plot(h_axis, np.zeros(HIST_N), color='#ffeb3b', lw=1.2)
ax_hist.set_xlim(-HISTORY_SEC, 0)
ax_hist.set_ylim(0, 0.5)
ax_hist.set_title(f'Volume History  ({HISTORY_SEC:.0f}s)', color='#ccccff', pad=5, fontsize=11)
ax_hist.set_xlabel('Waktu (s)', color='#7070aa', fontsize=9)
ax_hist.set_ylabel('RMS', color='#7070aa', fontsize=9)
ax_hist.axhline(0.04,  color='#ffff00', lw=0.8, ls='--', alpha=0.6)
ax_hist.axhline(0.15,  color='#ff4444', lw=0.8, ls='--', alpha=0.6)
ax_hist.grid(True, color='#1a1a3a', lw=0.5)
ax_hist.text(-HISTORY_SEC + 0.1, 0.042, 'normal', color='#ffff00', fontsize=7, alpha=0.7)
ax_hist.text(-HISTORY_SEC + 0.1, 0.152, 'keras',  color='#ff4444', fontsize=7, alpha=0.7)

# ── Info Panel ────────────────────────────────────────────
ax_info.axis('off')
info_text = ax_info.text(
    0.05, 0.95, 'Menunggu data...',
    transform=ax_info.transAxes,
    va='top', ha='left',
    color='#e0e0ff', fontsize=10.5,
    fontfamily='monospace',
    bbox=dict(boxstyle='round,pad=0.6', facecolor='#1a1a3a', alpha=0.85)
)

fig.suptitle('ESP32-S3-EYE  ─  Real-time Mic Analyzer',
             color='#ffffff', fontsize=13, fontweight='bold', y=0.98)

# ── Animasi update ────────────────────────────────────────
def update(_frame):
    with buf_lock:
        wave = waveform_buf.copy()
        hist = np.array(list(rms_history))

    # — Waveform —
    line_wave.set_ydata(wave)

    # — FFT —
    window  = np.hanning(FFT_SIZE)
    segment = wave[-FFT_SIZE:] if len(wave) >= FFT_SIZE else np.pad(wave, (FFT_SIZE - len(wave), 0))
    fft_mag = np.abs(np.fft.rfft(segment * window)) / (FFT_SIZE / 2)
    fft_db  = 20 * np.log10(np.maximum(fft_mag, 1e-9))
    line_fft.set_ydata(fft_db)

    # — History —
    line_hist.set_ydata(hist)
    for coll in ax_hist.collections:
        coll.remove()
    ax_hist.fill_between(h_axis, 0, hist, alpha=0.30, color='#ffeb3b')
    ax_hist.set_ylim(0, max(0.4, float(np.max(hist)) * 1.25))

    # — Metrics —
    rms  = float(np.sqrt(np.mean(wave ** 2)))
    peak = float(np.max(np.abs(wave)))

    rms_dbfs  = 20 * np.log10(rms  + 1e-9)
    peak_dbfs = 20 * np.log10(peak + 1e-9)

    # Estimasi noise floor (20 persentil amplitudo → saat sinyal ada, yg rendah = noise)
    noise_floor = float(np.percentile(np.abs(wave), 15))
    snr_db = 20 * np.log10((rms + 1e-9) / (noise_floor + 1e-9))
    snr_db = max(0.0, min(snr_db, 60.0))  # clamp ke range masuk akal

    # Frekuensi dominan (abaikan DC)
    dom_idx  = int(np.argmax(fft_mag[2:]) + 2)
    dom_freq = float(freqs[dom_idx])

    # Label status
    if rms < 0.004:
        status = "SENYAP"
        s_col  = '#888888'
    elif rms < 0.04:
        status = "NORMAL"
        s_col  = '#00e676'
    elif rms < 0.15:
        status = "KERAS"
        s_col  = '#ffeb3b'
    else:
        status = "SANGAT KERAS"
        s_col  = '#ff5252'

    if snr_db > 25:
        quality = "Sangat Baik ✓"
    elif snr_db > 15:
        quality = "Baik"
    elif snr_db > 8:
        quality = "Cukup"
    else:
        quality = "Berisik / Noise"

    conn_str = "TERHUBUNG" if connected.is_set() else "MENUNGGU..."

    info_text.set_text(
        f"Serial  : {conn_str}\n"
        f"\n"
        f"RMS     : {rms:.4f}  ({rms_dbfs:+.1f} dBFS)\n"
        f"Peak    : {peak:.4f}  ({peak_dbfs:+.1f} dBFS)\n"
        f"SNR est : {snr_db:.1f} dB  → {quality}\n"
        f"Dom.Freq: {dom_freq:.0f} Hz\n"
        f"\n"
        f"Status  : {status}\n"
        f"Sample  : {SAMPLE_RATE} Hz / 16-bit\n"
        f"Buffer  : {WAVE_N} samples / {WAVEFORM_SEC:.0f}s"
    )
    info_text.set_color(s_col if rms > 0.004 else '#888888')

    return line_wave, line_fft, line_hist, info_text


ani = animation.FuncAnimation(
    fig, update, interval=60, blit=False, cache_frame_data=False
)
plt.show()
