"""
mic_recorder.py
Rekam, tampilkan realtime, dan playback audio dari ESP32-S3-EYE.

Cara pakai:
  1. Upload 05-mic-record.ino ke board, TUTUP Serial Monitor Arduino IDE
  2. pip install -r requirements.txt
  3. python mic_recorder.py

Tombol GUI:
  [● REC]   - mulai rekam ke buffer
  [■ STOP]  - stop & simpan ke file WAV
  [▶ PLAY]  - putar rekaman terakhir lewat speaker
  [▶ OPEN]  - buka folder recordings di Explorer

Keyboard shortcut:
  R = REC,  S = STOP,  P = PLAY

File WAV disimpan di subfolder 'recordings/' (bisa dibuka VLC / WMP / dll)
"""

import os, sys, struct, threading, collections, wave, time, datetime, subprocess

import serial
import numpy as np
import sounddevice as sd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Button

# ── Konfigurasi ──────────────────────────────────────────────────────────────
PORT         = 'COM5'
BAUD         = 921600
SAMPLE_RATE  = 16000
MAGIC        = b'\xaa\x55\xaa\x55'

WAVEFORM_SEC = 1.0
HISTORY_SEC  = 5.0
FFT_SIZE     = 2048

WAVE_N  = int(SAMPLE_RATE * WAVEFORM_SEC)
HIST_N  = 200

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR   = os.path.join(SCRIPT_DIR, 'recordings')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── State bersama ─────────────────────────────────────────────────────────────
waveform_buf = np.zeros(WAVE_N, dtype=np.float32)
rms_history  = collections.deque(np.zeros(HIST_N), maxlen=HIST_N)
buf_lock     = threading.Lock()
connected    = threading.Event()

is_recording  = False
record_chunks = []          # list of np.int16 arrays
rec_lock      = threading.Lock()
rec_start_t   = 0.0

last_wav_path = None
last_wav_dur  = 0.0

is_playing   = False
status_msg   = 'Siap — tekan  ● REC  untuk mulai rekam'

# ── Serial reader thread ──────────────────────────────────────────────────────
def serial_reader():
    global waveform_buf, status_msg
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        connected.set()
        print(f'[OK] Serial terhubung: {PORT} @ {BAUD}')
    except serial.SerialException as e:
        status_msg = f'ERROR serial: {e}'
        print(f'[ERROR] {e}')
        return

    raw = bytearray()
    while True:
        try:
            incoming = ser.read(ser.in_waiting or 256)
        except Exception:
            break
        if not incoming:
            continue
        raw.extend(incoming)

        while True:
            idx = raw.find(MAGIC)
            if idx == -1:
                raw = bytearray(raw[-3:]) if len(raw) > 3 else raw
                break
            if idx > 0:
                raw = raw[idx:]
            if len(raw) < 6:
                break

            count     = struct.unpack_from('<H', raw, 4)[0]
            frame_end = 4 + 2 + count * 2
            if len(raw) < frame_end:
                break

            data_bytes  = raw[6:frame_end]
            raw         = raw[frame_end:]

            s_i16 = np.frombuffer(data_bytes, dtype='<i2').copy()
            s_f32 = s_i16.astype(np.float32) / 32768.0

            with buf_lock:
                waveform_buf = np.roll(waveform_buf, -len(s_f32))
                waveform_buf[-len(s_f32):] = s_f32
                rms_history.append(float(np.sqrt(np.mean(s_f32 ** 2))))

            if is_recording:
                with rec_lock:
                    record_chunks.append(s_i16)

threading.Thread(target=serial_reader, daemon=True).start()

# ── WAV helpers ───────────────────────────────────────────────────────────────
def save_wav(chunks, path):
    data = np.concatenate(chunks)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(data.tobytes())
    return len(data) / SAMPLE_RATE

def _play_thread(path):
    global is_playing, status_msg
    try:
        with wave.open(path, 'rb') as wf:
            raw_bytes = wf.readframes(wf.getnframes())
        data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        sd.play(data, SAMPLE_RATE)
        sd.wait()
    except Exception as e:
        status_msg = f'Play error: {e}'
    finally:
        is_playing   = False
        status_msg   = f'Selesai diputar: {os.path.basename(path)}'

# ── Button callbacks ──────────────────────────────────────────────────────────
def cb_rec(_event=None):
    global is_recording, record_chunks, rec_start_t, status_msg
    if is_recording or is_playing:
        return
    with rec_lock:
        record_chunks = []
    rec_start_t  = time.time()
    is_recording = True
    status_msg   = '● MEREKAM  —  tekan  ■ STOP  untuk simpan'
    print('[REC] Mulai rekam')

def cb_stop(_event=None):
    global is_recording, last_wav_path, last_wav_dur, status_msg
    if not is_recording:
        return
    is_recording = False
    with rec_lock:
        chunks = list(record_chunks)

    if not chunks:
        status_msg = 'Tidak ada data — coba REC lagi'
        return

    ts           = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    path         = os.path.join(OUTPUT_DIR, f'rec_{ts}.wav')
    last_wav_dur = save_wav(chunks, path)
    last_wav_path = path
    status_msg   = f'Tersimpan: rec_{ts}.wav  ({last_wav_dur:.1f}s)  — tekan ▶ PLAY'
    print(f'[STOP] {path}  ({last_wav_dur:.1f}s)')

def cb_play(_event=None):
    global is_playing, status_msg
    if last_wav_path is None:
        status_msg = 'Belum ada rekaman — tekan ● REC dulu'
        return
    if is_playing or is_recording:
        return
    is_playing = True
    status_msg = f'▶ Memutar: {os.path.basename(last_wav_path)}'
    threading.Thread(target=_play_thread, args=(last_wav_path,), daemon=True).start()

def cb_open(_event=None):
    subprocess.Popen(f'explorer "{OUTPUT_DIR}"')

# ── Figure layout ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(15, 10), facecolor='#0d0d1a')
fig.canvas.manager.set_window_title('ESP32-S3-EYE – Mic Recorder')

gs = GridSpec(3, 2, figure=fig,
              hspace=0.48, wspace=0.30,
              left=0.07, right=0.97, top=0.93, bottom=0.17)

ax_wave = fig.add_subplot(gs[0, :])
ax_fft  = fig.add_subplot(gs[1, :])
ax_hist = fig.add_subplot(gs[2, 0])
ax_info = fig.add_subplot(gs[2, 1])

BG = '#111128'
for ax in [ax_wave, ax_fft, ax_hist, ax_info]:
    ax.set_facecolor(BG)
    ax.tick_params(colors='#9090bb')
    for sp in ax.spines.values():
        sp.set_color('#2a2a5a')

# — Waveform —
t_axis    = np.linspace(0, WAVEFORM_SEC, WAVE_N)
line_wave, = ax_wave.plot(t_axis, np.zeros(WAVE_N), color='#00e676', lw=0.7)
ax_wave.set_xlim(0, WAVEFORM_SEC)
ax_wave.set_ylim(-1, 1)
ax_wave.set_xlabel('Waktu (s)', color='#7070aa', fontsize=9)
ax_wave.set_ylabel('Amplitude', color='#7070aa', fontsize=9)
ax_wave.axhline(0, color='#2a2a5a', lw=0.8)
ax_wave.grid(True, color='#1a1a3a', lw=0.5)
# indikator REC (titik merah berkedip di pojok kiri atas, dalam axes coords)
rec_dot = ax_wave.text(0.01, 0.88, '', transform=ax_wave.transAxes,
                        color='#ff3333', fontsize=16, fontweight='bold',
                        va='top')

# — FFT —
freqs     = np.fft.rfftfreq(FFT_SIZE, 1 / SAMPLE_RATE)
line_fft, = ax_fft.plot(freqs, np.full(len(freqs), -80.0), color='#ff6b6b', lw=0.9)
ax_fft.set_xlim(0, SAMPLE_RATE / 2)
ax_fft.set_ylim(-80, 0)
ax_fft.set_title('Spektrum Frekuensi (FFT)', color='#ccccff', pad=5, fontsize=11)
ax_fft.set_xlabel('Frekuensi (Hz)', color='#7070aa', fontsize=9)
ax_fft.set_ylabel('Level (dBFS)', color='#7070aa', fontsize=9)
ax_fft.grid(True, color='#1a1a3a', lw=0.5)
ax_fft.axvspan(80,   300,  alpha=0.06, color='#4466ff', label='Bass 80–300Hz')
ax_fft.axvspan(300,  3400, alpha=0.08, color='#44ff88', label='Suara 300–3400Hz')
ax_fft.axvspan(3400, 8000, alpha=0.04, color='#ffaa44', label='Treble >3.4kHz')
ax_fft.legend(loc='upper right', fontsize=7, facecolor='#111128',
              labelcolor='#aaaacc', framealpha=0.8)

# — History —
h_axis    = np.linspace(-HISTORY_SEC, 0, HIST_N)
line_hist, = ax_hist.plot(h_axis, np.zeros(HIST_N), color='#ffeb3b', lw=1.2)
ax_hist.set_xlim(-HISTORY_SEC, 0)
ax_hist.set_ylim(0, 0.5)
ax_hist.set_title(f'Volume RMS History ({HISTORY_SEC:.0f}s)', color='#ccccff', pad=5, fontsize=11)
ax_hist.set_xlabel('Waktu (s)', color='#7070aa', fontsize=9)
ax_hist.set_ylabel('RMS', color='#7070aa', fontsize=9)
ax_hist.grid(True, color='#1a1a3a', lw=0.5)
ax_hist.axhline(0.04, color='#ffff00', lw=0.8, ls='--', alpha=0.6)
ax_hist.axhline(0.15, color='#ff4444', lw=0.8, ls='--', alpha=0.6)
ax_hist.text(-HISTORY_SEC + 0.1, 0.042, 'normal', color='#ffff00', fontsize=7, alpha=0.7)
ax_hist.text(-HISTORY_SEC + 0.1, 0.152, 'keras',  color='#ff4444', fontsize=7, alpha=0.7)

# — Info panel —
ax_info.axis('off')
info_text = ax_info.text(
    0.05, 0.97, 'Menunggu data...',
    transform=ax_info.transAxes,
    va='top', ha='left',
    color='#e0e0ff', fontsize=10,
    fontfamily='monospace',
    bbox=dict(boxstyle='round,pad=0.6', facecolor='#1a1a3a', alpha=0.85)
)

fig.suptitle('ESP32-S3-EYE  ─  Mic Recorder & Analyzer',
             color='#ffffff', fontsize=13, fontweight='bold', y=0.98)

# ── Tombol GUI ────────────────────────────────────────────────────────────────
#  posisi: [left, bottom, width, height]  (figure fraction)
btn_specs = [
    ('● REC',     [0.07, 0.05, 0.16, 0.07], '#1e3a1e', '#2d5a2d', cb_rec),
    ('■ STOP',    [0.25, 0.05, 0.16, 0.07], '#1a1a3a', '#2a2a5a', cb_stop),
    ('▶ PLAY',    [0.43, 0.05, 0.16, 0.07], '#1a1a3a', '#2a2a5a', cb_play),
    ('📁 OPEN',   [0.61, 0.05, 0.16, 0.07], '#1a1a3a', '#2a2a5a', cb_open),
]

btn_objects = {}
for label, rect, col, hcol, cb in btn_specs:
    ax_b = fig.add_axes(rect)
    b    = Button(ax_b, label, color=col, hovercolor=hcol)
    b.label.set_color('#e0e0ff')
    b.label.set_fontsize(11)
    b.label.set_fontweight('bold')
    b.on_clicked(cb)
    btn_objects[label] = b

# Status bar (bawah)
ax_stat  = fig.add_axes([0.07, 0.01, 0.90, 0.03])
ax_stat.axis('off')
stat_txt = ax_stat.text(0.0, 0.5, status_msg,
                         transform=ax_stat.transAxes,
                         va='center', ha='left',
                         color='#aaaacc', fontsize=9,
                         fontfamily='monospace')

# ── Keyboard shortcuts ────────────────────────────────────────────────────────
def on_key(event):
    if event.key == 'r': cb_rec()
    elif event.key == 's': cb_stop()
    elif event.key == 'p': cb_play()

fig.canvas.mpl_connect('key_press_event', on_key)

# ── Animation ─────────────────────────────────────────────────────────────────
_blink = [True]

def update(_frame):
    # Ambil snapshot buffer
    with buf_lock:
        wave = waveform_buf.copy()
        hist = np.array(list(rms_history))

    # — Waveform —
    line_wave.set_ydata(wave)

    # Judul waveform + indikator REC berkedip
    if is_recording:
        _blink[0] = not _blink[0]
        elapsed   = time.time() - rec_start_t
        rec_dot.set_text('●' if _blink[0] else '')
        ax_wave.set_title(
            f'● MEREKAM  {elapsed:.1f}s  —  tekan S untuk stop',
            color='#ff4444', pad=5, fontsize=11)
    elif is_playing:
        rec_dot.set_text('')
        ax_wave.set_title('▶ MEMUTAR ...', color='#44ddff', pad=5, fontsize=11)
    else:
        rec_dot.set_text('')
        ax_wave.set_title('Waveform  (1 detik terakhir)',
                          color='#ccccff', pad=5, fontsize=11)

    # — FFT —
    window  = np.hanning(FFT_SIZE)
    seg     = (wave[-FFT_SIZE:] if len(wave) >= FFT_SIZE
               else np.pad(wave, (FFT_SIZE - len(wave), 0)))
    fft_mag = np.abs(np.fft.rfft(seg * window)) / (FFT_SIZE / 2)
    fft_db  = 20 * np.log10(np.maximum(fft_mag, 1e-9))
    line_fft.set_ydata(fft_db)

    # — History —
    line_hist.set_ydata(hist)
    for c in ax_hist.collections:
        c.remove()
    ax_hist.fill_between(h_axis, 0, hist, alpha=0.28, color='#ffeb3b')
    ax_hist.set_ylim(0, max(0.4, float(np.max(hist)) * 1.25))

    # — Metrics —
    rms  = float(np.sqrt(np.mean(wave ** 2)))
    peak = float(np.max(np.abs(wave)))
    rms_db  = 20 * np.log10(rms  + 1e-9)
    peak_db = 20 * np.log10(peak + 1e-9)
    noise   = float(np.percentile(np.abs(wave), 15))
    snr     = min(60.0, max(0.0, 20 * np.log10((rms + 1e-9) / (noise + 1e-9))))
    dom_f   = float(freqs[int(np.argmax(fft_mag[2:]) + 2)])

    if   rms < 0.004: status, sc = 'SENYAP',      '#888888'
    elif rms < 0.04:  status, sc = 'NORMAL',       '#00e676'
    elif rms < 0.15:  status, sc = 'KERAS',        '#ffeb3b'
    else:             status, sc = 'SANGAT KERAS', '#ff5252'

    quality = ('Sangat Baik ✓' if snr > 25 else
               'Baik'          if snr > 15 else
               'Cukup'         if snr > 8  else 'Berisik')

    rec_line = ''
    if last_wav_path:
        rec_line = (f'\n'
                    f'File    : {os.path.basename(last_wav_path)}\n'
                    f'Durasi  : {last_wav_dur:.1f}s')

    info_text.set_text(
        f"Serial  : {'TERHUBUNG' if connected.is_set() else 'MENUNGGU...'}\n"
        f"\n"
        f"RMS     : {rms:.4f}  ({rms_db:+.1f} dBFS)\n"
        f"Peak    : {peak:.4f}  ({peak_db:+.1f} dBFS)\n"
        f"SNR est : {snr:.1f} dB  → {quality}\n"
        f"Dom.Freq: {dom_f:.0f} Hz\n"
        f"Status  : {status}"
        + rec_line
    )
    info_text.set_color(sc)

    stat_txt.set_text(status_msg)

    return line_wave, line_fft, line_hist, info_text, rec_dot, stat_txt


ani = animation.FuncAnimation(
    fig, update, interval=60, blit=False, cache_frame_data=False
)

print(f'[INFO] File rekaman disimpan di: {OUTPUT_DIR}')
print('[INFO] Keyboard: R=REC  S=STOP  P=PLAY')
plt.show()
