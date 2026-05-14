#line 1 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\09-accelerometer\\README.md"
# 09 — Accelerometer QMA7981 (3-axis, I2C)

## Pendahuluan

Membaca data akselerometer 3-axis dari chip **QMA7981** (buatan QST Corporation) yang terpasang onboard pada YD-ESP32-S3-EYE. Data percepatan sumbu X, Y, Z dalam satuan **g** ditampilkan ke Serial UART setiap 100ms.

Chip dikonfirmasi melalui proses debugging bertahap:
- I2C Scanner → terdeteksi di alamat `0x12`
- Chip ID register `0x00` → mengembalikan `0xE7` (revisi QMA7981, bukan `0xE8` standard)
- Inisialisasi aktif memerlukan soft reset + delay 50ms + read-modify-write `REG_PM`

> **Chip:** QMA7981 (Chip ID `0xE7` = revisi silicon, bukan chip berbeda)
> **Interface:** I2C, shared dengan kamera OV2640 pada bus yang sama

---

## Pin Definition

| Sinyal | GPIO | Keterangan |
|--------|------|------------|
| SDA | 4 | I2C Data — shared dengan Camera SIOD |
| SCL | 5 | I2C Clock — shared dengan Camera SIOC |
| I2C Address | 0x12 | Fixed, tidak bisa diubah |

---

## Register Map QMA7981 (yang dipakai)

| Register | Addr | Nilai | Keterangan |
|----------|------|-------|------------|
| CHIP_ID | 0x00 | 0xE7 | ID chip (konfirmasi koneksi) |
| DX_L/H | 0x01–0x02 | — | Raw X 14-bit |
| DY_L/H | 0x03–0x04 | — | Raw Y 14-bit |
| DZ_L/H | 0x05–0x06 | — | Raw Z 14-bit |
| REG_RANGE | 0x0F | 0x04 | Range ±8g |
| REG_BW_ODR | 0x10 | 0x05 | Bandwidth 128Hz |
| REG_PM | 0x11 | 0x80 | Active mode |
| SOFT_RST | 0x36 | 0xB6 | Soft reset trigger |

**Format data 14-bit:**
```
raw = (MSB << 6) | (LSB >> 2)
if (raw & 0x2000) raw |= 0xC000;  // sign extend ke 16-bit
g = raw × (8.0 / 8192.0)          // skala ±8g
```

---

## Cara Kerja Program

1. **Soft reset** — tulis `0xB6` ke `0x36`, clear `0x00`, tunggu 50ms
2. **Cek Chip ID** — baca register `0x00`, terima `0xE7` atau `0xE8`
3. **Standby dulu** — baca `REG_PM`, clear bits `[1:0]`, tulis kembali
4. **Konfigurasi** — range `0x04` (±8g), bandwidth `0x05` (128Hz)
5. **Active mode** — tulis `0x80` ke `REG_PM`, tunggu 30ms
6. **Burst read** — baca 6 byte sekaligus mulai `REG_DX_L (0x01)`
7. **Konversi** — 14-bit signed → float dalam satuan g
8. **Print** — tampilkan X, Y, Z ke Serial setiap 100ms

---

## Alur Berpikir (Logic Flow)

```
SETUP:
  ├─ Wire.begin(GPIO4, GPIO5)
  ├─ writeReg(0x36, 0xB6)   // soft reset
  ├─ delay(50)
  ├─ writeReg(0x36, 0x00)   // clear reset
  ├─ readReg(0x00) → Chip ID check (0xE7 / 0xE8)
  │   └─ unknown → WARNING (lanjut)
  ├─ pm = readReg(0x11) & ~0x03  // standby
  ├─ writeReg(0x11, pm)
  ├─ writeReg(0x0F, 0x04)   // range ±8g
  ├─ writeReg(0x10, 0x05)   // BW 128Hz
  ├─ writeReg(0x11, 0x80)   // active mode
  └─ delay(30)

LOOP (setiap 100ms):
  ├─ beginTransmission(0x12) + write(0x01) + endTransmission(false)
  ├─ requestFrom(0x12, 6)   // burst read X,Y,Z
  ├─ buf[6] ← Wire.read() ×6
  ├─ parse: raw = (MSB<<6)|(LSB>>2), sign extend 14→16 bit
  ├─ float g = raw × (8.0/8192.0)
  └─ Serial.printf X, Y, Z
```

---

## Hasil

Board **datar di meja** (Z menghadap atas):
```
=== QMA Accelerometer ===
Chip ID : 0xE7 (QMA6100P)
Status  : OK, membaca data...

    X (g)         Y (g)         Z (g)
  ---------     ---------     ---------
  +0.0010      -0.0020      +1.0000
  +0.0010      -0.0020      +0.9980
```

Board **dimiringkan** → X/Y berubah, Z turun dari 1.0g:
```
  -0.2793      -0.6230      +0.3984
  -0.4912      +0.2070      +0.4707
```

> Vektor gravitasi selalu ≈ 1g: `√(X² + Y² + Z²) ≈ 1.0`

---

## Library yang Digunakan

| Library | Sumber | Keterangan |
|---------|--------|------------|
| `Wire.h` | Built-in Arduino ESP32 | I2C master driver |

> Tidak perlu library tambahan — semua komunikasi I2C dilakukan langsung via register.

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Chip ID error / salah | Jalankan `09-i2c-scanner` dulu untuk konfirmasi alamat |
| Semua nilai 0.0000 | Delay setelah soft reset kurang — pastikan `delay(50)` |
| ERROR: gagal baca | Cek koneksi I2C GPIO4/GPIO5 — periksa apakah kamera aktif bersamaan |
| Nilai Z jauh dari 1.0g | Normal kalau board digerakkan; taruh datar untuk verifikasi |
| Noise besar | Kurangi `REG_BW_ODR` ke 0x03 (64Hz) untuk filter lebih halus |
