#line 1 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\09-i2c-scanner\\README.md"
# 09 — I2C Scanner

## Pendahuluan

Tool diagnostik untuk mendeteksi semua perangkat I2C yang terhubung ke bus GPIO4 (SDA) dan GPIO5 (SCL) pada YD-ESP32-S3-EYE. Scan dilakukan setiap 5 detik dan menampilkan alamat yang merespon beserta nama chip yang dikenal.

Digunakan untuk memverifikasi keberadaan IMU QMA7981 sebelum menulis kode sensor, dan terbukti mendeteksi akselerometer onboard di alamat `0x12`.

---

## Pin Definition

| Sinyal | GPIO | Keterangan |
|--------|------|------------|
| SDA | 4 | I2C Data |
| SCL | 5 | I2C Clock |

> Bus I2C ini juga digunakan oleh kamera OV2640 (SIOD/SIOC) dan IMU QMA7981 — keduanya berbagi bus yang sama.

---

## Cara Kerja Program

1. `Wire.begin(4, 5)` — inisialisasi I2C pada GPIO4/5, clock 100kHz
2. Scan alamat `0x01` sampai `0x7F` satu per satu
3. Tiap alamat: `beginTransmission()` → `endTransmission()` → cek return code
   - `0` = ACK diterima → perangkat ada
   - `4` = error bus
4. Alamat yang merespon ditampilkan dengan nama chip jika dikenal
5. Scan diulang setiap 5 detik di `loop()`

---

## Hasil (YD-ESP32-S3-EYE)

```
=============================
   I2C Scanner - ESP32-S3
=============================
SDA = GPIO4 | SCL = GPIO5

Scanning I2C bus...
-----------------------------
  [FOUND] Addr = 0x12 ( 18)  <-- QMA7981 / QMA6100P (Accel)
-----------------------------
  Total ditemukan: 1 perangkat
=============================
```

**Kesimpulan:** Hanya 1 perangkat I2C onboard — akselerometer QMA7981 di `0x12`. Kamera OV2640 menggunakan bus I2C yang sama tetapi hanya aktif saat `esp_camera_init()` dipanggil.

---

## Library yang Digunakan

| Library | Sumber | Keterangan |
|---------|--------|------------|
| `Wire.h` | Built-in Arduino ESP32 | I2C master scan |

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Tidak ada perangkat ditemukan | Cek GPIO4/5 tidak di-override sketch lain; cek tegangan 3.3V |
| Error `4` di semua alamat | Bus I2C short atau pull-up resistor tidak ada |
| Alamat berbeda dari `0x12` | Bisa jadi board varian lain — catat alamat dan sesuaikan kode sensor |
