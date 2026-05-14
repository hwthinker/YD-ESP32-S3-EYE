#line 1 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\06-camera-stream\\README.md"
# 06 — Camera Stream (Live via Browser)

## Pendahuluan

Program live streaming kamera OV2640 pada ESP32-S3-EYE ke browser (HP atau PC) melalui WiFi. ESP32 bertindak sebagai Access Point mandiri — tidak memerlukan koneksi ke router eksternal. Program secara otomatis mendeteksi tipe sensor kamera dan melaporkannya di Serial Monitor.

**Hasil pengujian:** Sensor kamera pada board YD-ESP32-S3-EYE ini adalah **OV2640** (PID: `0x26`) — terkonfirmasi berjalan normal pada resolusi VGA (640×480).

Tujuan: streaming video JPEG/MJPEG via HTTP untuk monitoring visual nirkabel.

---

## Pin Definition

### Kamera OV2640

| Sinyal | GPIO | Sinyal | GPIO |
|--------|------|--------|------|
| XCLK | 15 | D0 (Y2) | 11 |
| SIOD (SDA) | 4 | D1 (Y3) | 9 |
| SIOC (SCL) | 5 | D2 (Y4) | 8 |
| VSYNC | 6 | D3 (Y5) | 10 |
| HREF | 7 | D4 (Y6) | 12 |
| PCLK | 13 | D5 (Y7) | 18 |
| PWDN | -1 (NC) | D6 (Y8) | 17 |
| RESET | -1 (NC) | D7 (Y9) | 16 |

### WiFi
- Mode: Access Point (AP)
- SSID: `ESP32-S3-EYE-CAM`
- Password: `12345678`
- IP: `192.168.4.1`

---

## Mekanisme Komunikasi (WiFi + HTTP MJPEG)

> **Tidak ada komunikasi LoRa.** Komunikasi menggunakan **WiFi 2.4 GHz** dengan protokol **HTTP** dan format **MJPEG (Motion JPEG)**.

### Arsitektur Komunikasi

```
┌──────────────────────┐         WiFi AP          ┌──────────────────┐
│   ESP32-S3-EYE       │                          │  HP / PC Client  │
│                       │  192.168.4.1:80          │                  │
│  Kamera OV2640 ──┐   │  ◄──────────────────►    │  Browser         │
│                  │   │   HTTP GET /              │  http://         │
│  Web Server ─────┤   │   HTTP GET /stream        │  192.168.4.1     │
│  (esp_http_server)│  │                           │                  │
│  WiFi AP ────────┘   │  MJPEG boundary:          │  <img src=       │
│                       │  multipart/x-mixed-replace│  "/stream">      │
└──────────────────────┘                          └──────────────────┘
```

### Protokol MJPEG Stream

Response HTTP menggunakan `Content-Type: multipart/x-mixed-replace;boundary=...` di mana setiap frame JPEG dikirim sebagai bagian terpisah:

```
--gc0p4Jq0M2Yt08jU534c0p
Content-Type: image/jpeg
Content-Length: 12345

<data JPEG 12345 bytes>
--gc0p4Jq0M2Yt08jU534c0p
Content-Type: image/jpeg
Content-Length: 12400

<data JPEG 12400 bytes>
...
```

Browser me-render stream ini secara native via tag `<img src="/stream">` — tidak memerlukan JavaScript khusus.

---

## Cara Kerja Program

1. **Inisialisasi Kamera** — `esp_camera_init()` dengan konfigurasi pin OV2640:
   - Pixel format: JPEG (kompresi hardware kamera)
   - Frame size: VGA (640×480)
   - JPEG quality: 12 (0=terbaik, 63=terburuk)
   - Frame buffer di PSRAM (8MB OPI)
2. **Deteksi Sensor** — Membaca `sensor->id.PID`, mencocokkan dengan PID yang dikenal (OV2640=0x26, OV7670=0x76, OV3660=0x36, OV5640=0x5640)
3. **Konfigurasi Sensor** — Jika OV2640: set auto white balance, auto exposure, auto gain
4. **WiFi Access Point** — `WiFi.softAP(SSID, PASS)` membuat AP dengan IP `192.168.4.1`
5. **Web Server** — `esp_http_server` melayani 2 endpoint:
   - `GET /` → Halaman HTML dengan tag `<img src="/stream">`
   - `GET /stream` → MJPEG stream (loop `esp_camera_fb_get()` → kirim frame JPEG)
6. **LED Indikator** — Berkedip setiap 2 detik, menampilkan jumlah client terhubung di Serial Monitor

---

## Alur Berpikir (Logic Flow)

```
SETUP:
  ├─ Serial.begin(115200)
  ├─ esp_camera_init(config)
  │   └─ Gagal? → blink LED cepat → STOP
  ├─ Deteksi sensor: baca PID
  │   ├─ 0x26 → OV2640 ✓ → set auto exposure/white balance/gain
  │   └─ lain → tampilkan nama sensor
  ├─ WiFi.mode(WIFI_AP) + WiFi.softAP(SSID, PASS)
  ├─ Tampilkan info akses: SSID, Password, URL
  ├─ startWebServer()
  │   ├─ httpd_start() di port 80
  │   ├─ Daftarkan GET / → index_handler (HTML)
  │   └─ Daftarkan GET /stream → stream_handler (MJPEG)
  └─ LED nyala → SIAP

LOOP:
  └─ Setiap 2 detik:
      ├─ Toggle LED
      └─ Cetak jumlah client: WiFi.softAPgetStationNum()

STREAM HANDLER (loop internal):
  ├─ fb = esp_camera_fb_get()
  │   └─ NULL? → WARN → break
  ├─ Jika format != JPEG → frame2jpg(fb, 80)
  ├─ Kirim header multipart + data JPEG
  │   ├─ httpd_resp_send_chunk(header)
  │   └─ httpd_resp_send_chunk(jpeg_data)
  ├─ esp_camera_fb_return(fb)
  └─ Kembali ke atas → frame berikutnya
```

---

## Hasil

### Serial Monitor Output

```
╔══════════════════════════════════════╗
║  ESP32-S3-EYE  ─  Camera Stream     ║
╚══════════════════════════════════════╝
Inisialisasi kamera... OK
Sensor PID: 0x26  → OV2640 ✓

╔══════════════════════════════════════╗
║  KAMERA SIAP — CARA AKSES:           ║
╠══════════════════════════════════════╣
║  WiFi SSID : ESP32-S3-EYE-CAM        ║
║  Password  : 12345678                ║
║  URL       : http://192.168.4.1      ║
╠══════════════════════════════════════╣
║  1. Sambung HP/PC ke WiFi di atas    ║
║  2. Buka browser, ketik URL di atas  ║
║  3. Nikmati live stream kamera!      ║
╚══════════════════════════════════════╝
[STATUS] Klien terhubung: 1
```

### Tampilan Browser

Halaman web minimalis dengan:
- Judul: "ESP32-S3-EYE — Live Camera"
- Gambar live stream MJPEG
- Informasi tambahan di footer

---

## Library yang Digunakan

| Library | Sumber | Keterangan |
|---------|--------|------------|
| `esp_camera.h` | Built-in ESP32 Arduino Core | Driver kamera + sensor auto-detect |
| `esp_http_server.h` | Built-in ESP32 Arduino Core | HTTP server untuk MJPEG stream |
| `WiFi.h` | Built-in ESP32 Arduino Core | WiFi AP mode |

> Semua library sudah built-in — tidak perlu instalasi tambahan.

---

## Cara Instal Library

Tidak diperlukan instalasi library tambahan. Semua library (`esp_camera`, `esp_http_server`, `WiFi`) sudah termasuk dalam ESP32 Arduino Core.

**Pengaturan Board WAJIB:**
- **PSRAM**: OPI PSRAM
- **Partition Scheme**: Huge APP (3MB No OTA/1MB SPIFFS)

---

## Cara Pakai

1. Upload sketch ke ESP32-S3-EYE
2. Buka Serial Monitor (115200 baud) — tunggu info WiFi muncul
3. Di HP/PC: sambung ke WiFi `ESP32-S3-EYE-CAM` (password `12345678`)
4. Buka browser → `http://192.168.4.1`
5. Live stream muncul otomatis

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `Inisialisasi kamera... GAGAL` | Pastikan **PSRAM = OPI PSRAM** dan **Partition = Huge APP** |
| LED berkedip cepat setelah upload | Error inisialisasi kamera — cek setting PSRAM/Partition |
| Browser tidak bisa buka URL | Pastikan HP/PC terhubung ke WiFi `ESP32-S3-EYE-CAM` |
| Gambar patah-patah / lambat | Normal untuk WiFi AP — dekatkan ke board |
| Gambar terbalik | Ubah `s->set_vflip(s, 1)` atau `s->set_hmirror(s, 1)` |
| Tidak bisa upload (board tidak cukup space) | Pastikan Partition Scheme = Huge APP |
