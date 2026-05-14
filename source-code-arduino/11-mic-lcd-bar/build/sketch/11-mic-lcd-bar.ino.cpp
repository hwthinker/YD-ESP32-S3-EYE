#include <Arduino.h>
#line 1 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\11-mic-lcd-bar\\11-mic-lcd-bar.ino"
/*
 * 11-mic-lcd-bar.ino
 * Test & Monitoring Mikrofon I2S dengan visualisasi bar pada LCD ST7789V
 *
 * Board   : ESP32S3 Dev Module
 * USB Mode: Hardware CDC and JTAG
 * PSRAM   : OPI PSRAM
 */

#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include <esp_system.h>
#include <driver/i2s.h>

// ── Pin LCD ──────────────────────────────────────────────
#define TFT_MOSI  47
#define TFT_SCLK  21
#define TFT_CS    44
#define TFT_DC    43
#define TFT_RST   -1
#define TFT_BL    48

Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);

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
#define SCALE_MAX      3500           // nilai RMS untuk bar penuh (kalibrasi dari hasil nyata)
#define THRESH_SENYAP    60           // noise floor board ~30
#define THRESH_NORMAL   400
#define THRESH_KERAS   1500

int32_t raw[READ_BUF_SAMPLES];

// State untuk UI
int lastBarWidth = 0;
String lastStatus = "";

#line 50 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\11-mic-lcd-bar\\11-mic-lcd-bar.ino"
void setup();
#line 133 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\11-mic-lcd-bar\\11-mic-lcd-bar.ino"
void loop();
#line 50 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\11-mic-lcd-bar\\11-mic-lcd-bar.ino"
void setup() {
  Serial.begin(115200);

  // ── INIT LCD ──────────────────────────────────────────────
  pinMode(TFT_CS, OUTPUT);
  digitalWrite(TFT_CS, HIGH);
  pinMode(TFT_DC, OUTPUT);
  digitalWrite(TFT_DC, HIGH);

  if (esp_reset_reason() == ESP_RST_POWERON) {
    delay(200);
    ESP.restart();
  }
  delay(50);

  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, LOW);

  SPI.begin(TFT_SCLK, -1, TFT_MOSI);
  tft.init(240, 240);
  tft.setRotation(2);

  tft.fillScreen(0x0841); // Biru gelap
  tft.fillRect(0, 0, 240, 4, 0x07FF);   // Cyan atas
  tft.fillRect(0, 236, 240, 4, 0x07FF); // Cyan bawah

  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(15, 20);
  tft.print("Audio Level");

  tft.drawFastHLine(10, 45, 220, 0x07FF);

  // ── INIT I2S ──────────────────────────────────────────────
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

  if (i2s_driver_install(I2S_PORT, &cfg, 0, NULL) != ESP_OK) {
    tft.setTextColor(ST77XX_RED);
    tft.setCursor(10, 60);
    tft.print("I2S Install Err");
    while (true) delay(1000);
  }

  if (i2s_set_pin(I2S_PORT, &pins) != ESP_OK) {
    tft.setTextColor(ST77XX_RED);
    tft.setCursor(10, 60);
    tft.print("I2S Pin Err");
    while (true) delay(1000);
  }

  i2s_zero_dma_buffer(I2S_PORT);
  delay(200);

  // Label RMS & Status awal
  tft.setTextColor(0x8410); // Abu-abu
  tft.setTextSize(1);
  tft.setCursor(10, 160);
  tft.print("RMS Value:");
  
  // Gambar outline untuk bar graph agar statis
  tft.drawRect(9, 99, 222, 32, 0xFFFF); // Kotak bingkai putih
}

void loop() {
  size_t bytesRead = 0;
  esp_err_t res = i2s_read(I2S_PORT, raw, sizeof(raw), &bytesRead, pdMS_TO_TICKS(200));

  if (res != ESP_OK || bytesRead == 0) {
    delay(10);
    return;
  }

  int n = bytesRead / sizeof(int32_t);
  int64_t sumSq = 0;
  
  for (int i = 0; i < n; i++) {
    int32_t s = raw[i] >> 14;
    sumSq += (int64_t)s * s;
  }

  long rms = (long)sqrt((double)sumSq / n);

  // -- Update UI LCD --

  // 1. Tentukan warna dan status teks
  uint16_t barColor = ST77XX_GREEN;
  String currentStatus = "SENYAP";
  uint16_t statusColor = ST77XX_WHITE;

  if (rms < THRESH_SENYAP) {
    barColor = ST77XX_CYAN;
    currentStatus = "SENYAP";
    statusColor = ST77XX_CYAN;
  } else if (rms < THRESH_NORMAL) {
    barColor = ST77XX_GREEN;
    currentStatus = "NORMAL";
    statusColor = ST77XX_GREEN;
  } else if (rms < THRESH_KERAS) {
    barColor = ST77XX_YELLOW;
    currentStatus = "KERAS";
    statusColor = ST77XX_YELLOW;
  } else {
    barColor = ST77XX_RED;
    currentStatus = "SGT KERAS";
    statusColor = ST77XX_RED;
  }

  // 2. Gambar Bar Graph (Posisi Y: 100, X: 10, Lebar max: 220, Tinggi: 30)
  int maxWidth = 220;
  int currentBarWidth = map(constrain(rms, 0, SCALE_MAX), 0, SCALE_MAX, 0, maxWidth);

  if (currentBarWidth != lastBarWidth || barColor != ST77XX_GREEN) { 
    if (currentBarWidth > lastBarWidth) {
      tft.fillRect(10 + lastBarWidth, 100, currentBarWidth - lastBarWidth, 30, barColor);
    } else if (currentBarWidth < lastBarWidth) {
      tft.fillRect(10 + currentBarWidth, 100, lastBarWidth - currentBarWidth, 30, 0x0841); 
    }
    // Update bagian isi untuk ganti warna
    tft.fillRect(10, 100, currentBarWidth, 30, barColor); 
    lastBarWidth = currentBarWidth;
  }

  // 3. Update Teks Status (jika berubah)
  if (currentStatus != lastStatus) {
    tft.fillRect(10, 60, 220, 20, 0x0841); // Clear area teks
    tft.setTextColor(statusColor);
    tft.setTextSize(2);
    tft.setCursor(10, 60);
    tft.print(currentStatus);
    lastStatus = currentStatus;
  }

  // 4. Update Angka RMS (Posisi X: 80, Y: 160)
  tft.fillRect(80, 160, 100, 10, 0x0841); 
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(1);
  tft.setCursor(80, 160);
  tft.print(rms);

  delay(40); // Kecepatan refresh UI
}

