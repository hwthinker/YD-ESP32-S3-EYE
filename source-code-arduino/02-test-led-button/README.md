# 02 — Test LED & Button

## Pendahuluan

Program uji coba LED onboard dan keempat tombol fungsi (UP/DOWN/PLAY/MENU) serta tombol BOOT pada YD-ESP32-S3-EYE. Tombol fungsi dibaca melalui satu pin ADC (GPIO1) dengan teknik resistor ladder — setiap tombol menghasilkan tegangan berbeda.

Tujuan: memvalidasi seluruh input fisik board (5 tombol + 1 LED).

---

## Pin Definition

| Komponen | GPIO | Mode | Keterangan |
|----------|------|------|------------|
| LED | 3 | OUTPUT | HIGH = nyala |
| BOOT Button | 0 | INPUT_PULLUP | LOW saat ditekan |
| Function Button | 1 | ADC | UP/DOWN/PLAY/MENU via resistor ladder |

### Mapping ADC Tombol Fungsi

| Tombol | Nilai ADC (approx) | Range Deteksi | Aksi |
|--------|---------------------|---------------|------|
| UP | ~413 | 300 – 600 | LED ON |
| DOWN | ~923 | 800 – 1100 | LED OFF |
| PLAY | ~2328 | 2100 – 2500 | Cetak "PLAY" |
| MENU | ~2861 | 2700 – 3000 | Cetak "MENU" |
| Tidak ditekan | ≥ 3500 | — | Tidak ada aksi |

> Nilai ADC bisa sedikit berbeda antar board. Threshold menggunakan range lebar untuk toleransi.

---

## Cara Kerja Program

1. **Inisialisasi** — LED pin sebagai OUTPUT (default OFF), BOOT pin sebagai INPUT_PULLUP.
2. **Loop utama** membaca dua sumber input setiap iterasi:
   - **Tombol BOOT (digital)** — Deteksi transisi HIGH→LOW (falling edge) untuk toggle LED. `lastBoot` menyimpan state sebelumnya untuk mencegah repeat trigger.
   - **Tombol Fungsi (ADC)** — `analogRead(GPIO1)` membaca tegangan. Jika ADC < 3500 (ada tombol ditekan), nilai dibandingkan dengan range threshold masing-masing tombol.
3. **Debounce** — `delay(250)` setelah deteksi tombol fungsi, `delay(200)` setelah BOOT toggle.

---

## Alur Berpikir (Logic Flow)

```
LOOP:
  │
  ├─ Baca BOOT button (digital)
  │   └─ Transisi HIGH→LOW? → Toggle LED ON/OFF → delay(200)
  │
  ├─ Baca ADC (GPIO1)
  │   └─ ADC < 3500? (ada tombol ditekan)
  │       ├─ 300 < ADC < 600   → "UP"   → LED ON
  │       ├─ 800 < ADC < 1100  → "DOWN" → LED OFF
  │       ├─ 2100 < ADC < 2500 → "PLAY" → cetak
  │       └─ 2700 < ADC < 3000 → "MENU" → cetak
  │       delay(250)
  │
  └─ delay(10) → kembali ke LOOP
```

---

## Hasil

**Serial Monitor Output (baud 115200):**

```
--- ESP32-S3-EYE Reverted to Stable ---
BOOT: ON
Tombol: UP -> LED ON
Tombol: DOWN -> LED OFF
Tombol: PLAY
Tombol: MENU
BOOT: OFF
```

---

## Library yang Digunakan

Tidak ada library eksternal. Hanya menggunakan fungsi built-in Arduino:
- `pinMode()`, `digitalRead()`, `digitalWrite()` — GPIO digital
- `analogRead()` — ADC reading
- `Serial` — Output monitoring

---

## Cara Instal Library

Tidak diperlukan instalasi library tambahan.

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Tombol tidak terdeteksi | Cek nilai ADC mentah dengan `Serial.println(analogRead(1))` dan sesuaikan threshold |
| LED tidak menyala | Pastikan `LED_PIN` adalah GPIO 3 |
| Tombol trigger berulang | Naikkan nilai `delay()` setelah deteksi tombol |
| BOOT tidak berfungsi | Pastikan mode pin adalah `INPUT_PULLUP` |
