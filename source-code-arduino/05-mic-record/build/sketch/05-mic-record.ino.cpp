#include <Arduino.h>
#line 1 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\05-mic-record\\05-mic-record.ino"
/*
 * 05-mic-record.ino
 * Stream audio I2S ke komputer via Serial USB (identik dengan 04-mic-stream)
 * Format paket: [MAGIC 4B][count:uint16_LE][data:int16_LE * count]
 *
 * Board    : ESP32S3 Dev Module / espressif_esp32s3_eye
 * Baud     : 921600
 * Output   : PCM 16-bit signed, 16kHz, mono
 *
 * Mic pins:
 *   WS  → GPIO 42
 *   SCK → GPIO 41
 *   SD  → GPIO  2
 */

#include <driver/i2s.h>

#define MIC_WS   42
#define MIC_SCK  41
#define MIC_SD    2

#define I2S_PORT        I2S_NUM_0
#define SAMPLE_RATE     16000
#define DMA_BUF_COUNT   8
#define DMA_BUF_LEN     256
#define CHUNK_SAMPLES   256

static const uint8_t MAGIC[4] = {0xAA, 0x55, 0xAA, 0x55};

int32_t raw32[CHUNK_SAMPLES];
int16_t pcm16[CHUNK_SAMPLES];

#line 33 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\05-mic-record\\05-mic-record.ino"
void setup();
#line 64 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\05-mic-record\\05-mic-record.ino"
void loop();
#line 33 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\05-mic-record\\05-mic-record.ino"
void setup() {
  Serial.begin(921600);

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

  i2s_driver_install(I2S_PORT, &cfg, 0, NULL);
  i2s_set_pin(I2S_PORT, &pins);
  i2s_zero_dma_buffer(I2S_PORT);
  delay(300);
}

void loop() {
  size_t bytesRead = 0;
  i2s_read(I2S_PORT, raw32, sizeof(raw32), &bytesRead, pdMS_TO_TICKS(100));

  int n = bytesRead / sizeof(int32_t);
  if (n == 0) return;

  for (int i = 0; i < n; i++) {
    pcm16[i] = (int16_t)(raw32[i] >> 16);
  }

  uint16_t count = (uint16_t)n;
  Serial.write(MAGIC, 4);
  Serial.write((uint8_t*)&count, 2);
  Serial.write((uint8_t*)pcm16, n * 2);
}

