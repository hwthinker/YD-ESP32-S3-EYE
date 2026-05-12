# 02 — Test LED & Button

Test LED onboard dan keempat tombol fungsi (UP / DOWN / PLAY / MENU) serta tombol BOOT pada ESP32-S3-EYE.

---

## Hardware

| Komponen     | GPIO | Keterangan                          |
|--------------|------|-------------------------------------|
| LED          | 3    | OUTPUT — HIGH = nyala               |
| Tombol BOOT  | 0    | INPUT\_PULLUP — toggle LED          |
| Tombol Fungsi| 1    | ADC — UP / DOWN / PLAY / MENU       |

### Mapping ADC Tombol Fungsi

| Tombol | Nilai ADC (approx) | Aksi default  |
|--------|--------------------|---------------|
| UP     | ~413               | LED ON        |
| DOWN   | ~923               | LED OFF       |
| PLAY   | ~2328              | Cetak "PLAY"  |
| MENU   | ~2861              | Cetak "MENU"  |

> Nilai ADC bisa sedikit berbeda antar board. Tidak ada tombol yang ditekan → ADC ≥ 3500.

---

## Arduino IDE Settings

| Setting            | Nilai                  |
|--------------------|------------------------|
| Board              | ESP32S3 Dev Module     |
| Port               | COM5 (sesuaikan)       |
| Upload Speed       | 921600                 |
| USB Mode           | Hardware CDC and JTAG  |

---

## Cara Upload

1. Buka `02-test-led-button.ino` di Arduino IDE
2. Pilih board dan port
3. Klik **Upload**
4. Buka **Serial Monitor** → baud **115200**

---

## Cara Pakai

| Aksi               | Hasil                    |
|--------------------|--------------------------|
| Tekan BOOT         | Toggle LED ON/OFF        |
| Tekan UP           | LED ON                   |
| Tekan DOWN         | LED OFF                  |
| Tekan PLAY         | Cetak "Tombol: PLAY"     |
| Tekan MENU         | Cetak "Tombol: MENU"     |

---

## Expected Output Serial Monitor

```
--- ESP32-S3-EYE Reverted to Stable ---
BOOT: ON
Tombol: UP -> LED ON
Tombol: DOWN -> LED OFF
Tombol: PLAY
Tombol: MENU
```

---

## Troubleshoot

| Masalah | Solusi |
|---------|--------|
| Tombol tidak terdeteksi | Cek nilai ADC dengan `Serial.println(analogRead(1))` dan sesuaikan threshold |
| LED tidak menyala | Pastikan `LED_PIN` adalah GPIO 3 |
