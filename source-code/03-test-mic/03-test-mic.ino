/*
 * 03-test-mic.ino
 * Test & Monitoring Mikrofon I2S pada ESP32-S3-EYE
 *
 * Board   : ESP32S3 Dev Module (atau espressif_esp32s3_eye)
 * Library : driver/i2s.h  (built-in ESP32 Arduino Core >= 2.x)
 *
 * Pinout Mikrofon (I2S Digital - MSM261S4030H0):
 *   I2S_WS  (LRCK / Word Select) : GPIO 42
 *   I2S_SCK (BCK  / Bit Clock)   : GPIO 41
 *   I2S_SD  (DATA / Serial Data) : GPIO  2
 *
 * Cara pakai:
 *   1. Upload sketch ini ke ESP32-S3-EYE
 *   2. Buka Serial Monitor, baud 115200
 *   3. Bicara/tepuk tangan dekat board
 *   4. Lihat bar graph dan label status berubah
 *
 * Troubleshoot:
 *   - Kalau RMS selalu 0 → pin WS/SCK/DATA salah atau mic tidak ada
 *   - Kalau RMS sangat tinggi tanpa suara → offset DC, coba shift lain
 *   - Kalau error saat install driver → pastikan I2S_PORT belum dipakai library lain
 */

#include <driver/i2s.h>

// ── Pin Mikrofon ─────────────────────────────────────────
#define MIC_WS   42
#define MIC_SCK  41
#define MIC_SD    2

// ── Konfigurasi I2S ──────────────────────────────────────
#define I2S_PORT       I2S_NUM_0
#define SAMPLE_RATE    16000          // Hz
#define DMA_BUF_COUNT      4
#define DMA_BUF_LEN      512          // samples per DMA buffer
#define READ_BUF_SAMPLES 512

// ── Threshold visualisasi ────────────────────────────────
#define BAR_WIDTH        40           // karakter lebar bar graph
#define SCALE_MAX      3500           // nilai RMS untuk bar penuh (kalibrasi dari hasil nyata)
#define THRESH_SENYAP    60           // noise floor board ~30
#define THRESH_NORMAL   400
#define THRESH_KERAS   1500

// ── Buffer baca ─────────────────────────────────────────-
int32_t raw[READ_BUF_SAMPLES];

// ─────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("╔════════════════════════════════════════════╗");
  Serial.println("║  ESP32-S3-EYE  ─  MIC TEST & MONITOR      ║");
  Serial.println("╚════════════════════════════════════════════╝");
  Serial.println();
  Serial.printf("  Mic pins  : WS=%d  SCK=%d  DATA=%d\n", MIC_WS, MIC_SCK, MIC_SD);
  Serial.printf("  Sample rate: %d Hz\n", SAMPLE_RATE);
  Serial.println();
  Serial.println("Inisialisasi I2S driver...");

  // Konfigurasi I2S
  i2s_config_t cfg = {
    .mode                 = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate          = SAMPLE_RATE,
    .bits_per_sample      = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format       = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags     = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count        = DMA_BUF_COUNT,
    .dma_buf_len          = DMA_BUF_LEN,
    .use_apll             = false,
    .tx_desc_auto_clear   = false,
    .fixed_mclk           = 0
  };

  i2s_pin_config_t pins = {
    .mck_io_num   = I2S_PIN_NO_CHANGE,
    .bck_io_num   = MIC_SCK,
    .ws_io_num    = MIC_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num  = MIC_SD
  };

  esp_err_t err = i2s_driver_install(I2S_PORT, &cfg, 0, NULL);
  if (err != ESP_OK) {
    Serial.printf("  [ERROR] Gagal install I2S driver: 0x%x\n", err);
    Serial.println("  → Cek apakah library lain sudah pakai I2S_NUM_0");
    while (true) delay(1000);
  }

  err = i2s_set_pin(I2S_PORT, &pins);
  if (err != ESP_OK) {
    Serial.printf("  [ERROR] Gagal set pin I2S: 0x%x\n", err);
    while (true) delay(1000);
  }

  // Flush buffer awal (buang sample pertama yang sering noise)
  i2s_zero_dma_buffer(I2S_PORT);
  delay(200);

  Serial.println("  [OK] Mikrofon siap!");
  Serial.println();
  Serial.println("  Bicara atau tepuk tangan dekat board...");
  Serial.println();
  Serial.println("  RMS    Peak   | Bar (0──────────max) | Status");
  Serial.println("  ─────────────────────────────────────────────");
}

// ─────────────────────────────────────────────────────────
void printBar(long value, long maxVal) {
  int filled = (int)map(constrain(value, 0, maxVal), 0, maxVal, 0, BAR_WIDTH);
  Serial.print("|");
  for (int i = 0; i < BAR_WIDTH; i++) {
    if (i < filled) {
      // gradasi karakter: tenang='.', sedang=':', keras='|', puncak='█'
      if      (i < BAR_WIDTH * 0.4) Serial.print(":");
      else if (i < BAR_WIDTH * 0.7) Serial.print("|");
      else                           Serial.print("#");
    } else {
      Serial.print(".");
    }
  }
  Serial.print("|");
}

void printStatus(long rms) {
  if      (rms < THRESH_SENYAP) Serial.println(" [  SENYAP  ]");
  else if (rms < THRESH_NORMAL) Serial.println(" [  normal  ]");
  else if (rms < THRESH_KERAS)  Serial.println(" [  KERAS   ]");
  else                          Serial.println(" [!!SANGAT KERAS!!]");
}

// ─────────────────────────────────────────────────────────
void loop() {
  size_t bytesRead = 0;

  esp_err_t res = i2s_read(
    I2S_PORT,
    raw,
    sizeof(raw),
    &bytesRead,
    pdMS_TO_TICKS(200)
  );

  if (res != ESP_OK) {
    Serial.printf("  [ERROR] i2s_read gagal: 0x%x\n", res);
    delay(500);
    return;
  }

  if (bytesRead == 0) {
    Serial.println("  [WARN] Tidak ada data dari mikrofon, cek koneksi!");
    delay(300);
    return;
  }

  int n = bytesRead / sizeof(int32_t);

  // Hitung RMS dan Peak (normalisasi 32-bit → 18-bit efektif untuk MSM261)
  int64_t sumSq = 0;
  int32_t peak  = 0;
  for (int i = 0; i < n; i++) {
    // Geser kanan 14 bit: buang noise LSB, simpan 18 bit atas
    int32_t s = raw[i] >> 14;
    sumSq += (int64_t)s * s;
    if (abs(s) > abs(peak)) peak = s;
  }

  long rms = (long)sqrt((double)sumSq / n);

  // Cetak baris monitoring (peak ditampilkan absolut karena audio signed)
  Serial.printf("  %5ld  %6ld  ", rms, (long)abs(peak));
  printBar(rms, SCALE_MAX);
  printStatus(rms);

  delay(80);   // ~12 update per detik
}
