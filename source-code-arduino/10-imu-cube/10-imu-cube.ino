/*
 * 10-imu-cube.ino
 * 3D Wireframe Cube - tilt the board, the cube stays level in world-space
 * Board:  YD-ESP32-S3-EYE
 * LCD:    ST7789V 240x240  SPI  (MOSI=47 SCK=21 CS=44 DC=43 BL=48)
 * Sensor: QMA7981 3-axis accelerometer  I2C  (SDA=4 SCL=5 addr=0x12)
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include <esp_system.h>

/* -- TFT pins ------------------------------------------ */
#define TFT_MOSI  47
#define TFT_SCLK  21
#define TFT_CS    44
#define TFT_DC    43
#define TFT_RST   -1          /* no RST gpio - tied to board EN */
#define TFT_BL    48          /* P-channel MOSFET: LOW = ON    */

/* -- QMA7981 Accelerometer ----------------------------- */
#define QMA_ADDR     0x12     /* fixed I2C address */
#define SDA_PIN      4
#define SCL_PIN      5

#define REG_CHIP_ID  0x00
#define REG_DX_L     0x01
#define REG_RANGE    0x0F
#define REG_BW_ODR   0x10
#define REG_PM       0x11
#define REG_SOFT_RST 0x36

/* +/-8g full-scale, 14-bit signed */
#define SCALE_G  (8.0f / 8192.0f)

/* -- Cube visual parameters ---------------------------- */
const float  CUBE_SIZE   = 280.0f;  /* half-size in pixels  */
const float  PERSP_DIST  =   4.5f;  /* perspective factor   */
const int    SCREEN_CX   =  120;    /* display centre X     */
const int    SCREEN_CY   =  120;    /* display centre Y     */
const float  SENSITIVITY =  1.4f;   /* tilt -> angle gain   */
const float  SMOOTH      =  0.08f;  /* low-pass filter      */

Adafruit_ST7789 tft(TFT_CS, TFT_DC, TFT_RST);

/* -- Unit cube geometry -------------------------------- */
/* 8 vertices (normalised) */
static const float verts[8][3] = {
  {-1, -1, -1}, { 1, -1, -1}, { 1,  1, -1}, {-1,  1, -1},
  {-1, -1,  1}, { 1, -1,  1}, { 1,  1,  1}, {-1,  1,  1}
};

/* 12 edges - front-face, back-face, connectors */
static const uint8_t edges[12][2] = {
  {0, 1}, {1, 2}, {2, 3}, {3, 0},   /* near face */
  {4, 5}, {5, 6}, {6, 7}, {7, 4},   /* far face  */
  {0, 4}, {1, 5}, {2, 6}, {3, 7}    /* connectors */
};

/* -- QMA7981 low-level I2C helpers --------------------- */
static uint8_t readReg(uint8_t reg) {
  Wire.beginTransmission(QMA_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(QMA_ADDR, (uint8_t)1);
  return Wire.available() ? Wire.read() : 0xFF;
}

static void writeReg(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(QMA_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

static bool readXYZ(float &ax, float &ay, float &az) {
  Wire.beginTransmission(QMA_ADDR);
  Wire.write(REG_DX_L);
  if (Wire.endTransmission(false) != 0) return false;
  Wire.requestFrom(QMA_ADDR, (uint8_t)6);
  if (Wire.available() < 6) return false;

  uint8_t b[6];
  for (int i = 0; i < 6; i++) b[i] = Wire.read();

  /* 14-bit signed -> sign-extend to 16-bit */
  auto to14 = [](uint8_t lsb, uint8_t msb) -> int16_t {
    int16_t v = (int16_t)((msb << 6) | (lsb >> 2));
    if (v & 0x2000) v |= (int16_t)0xC000;
    return v;
  };

  ax = to14(b[0], b[1]) * SCALE_G;
  ay = to14(b[2], b[3]) * SCALE_G;
  az = to14(b[4], b[5]) * SCALE_G;
  return true;
}

/* ------------------------------------------------------ */
void setup() {
  /* 1. LCD pre-init (cold-boot fix) */
  pinMode(TFT_CS, OUTPUT);
  digitalWrite(TFT_CS, HIGH);         /* de-select LCD while GPIO stabilises */

  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, LOW);          /* P-channel: LOW = ON */

  if (esp_reset_reason() == ESP_RST_POWERON) {
    delay(200);
    ESP.restart();                    /* re-boot -> GPIO Hi-Z */
  }

  delay(50);
  SPI.begin(TFT_SCLK, -1, TFT_MOSI);
  tft.init(240, 240);
  tft.setRotation(2);

  /* 2. Boot splash */
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(3);
  tft.setCursor(50, 55);
  tft.print("IMU");
  tft.setTextSize(2);
  tft.setCursor(45, 95);
  tft.print("CUBE");
  tft.setTextSize(1);
  tft.setTextColor(0x8410);           /* dark grey */
  tft.setCursor(20, 145);
  tft.print("YD-ESP32-S3-EYE");

  /* progress bar while sensor inits */
  tft.drawRect(30, 170, 180, 6, 0x8410);
  for (int i = 0; i <= 180; i += 15) {
    tft.fillRect(31 + i, 171, 12, 4, ST77XX_CYAN);
    delay(40);
  }

  /* 3. QMA7981 init */
  Wire.begin(SDA_PIN, SCL_PIN);
  delay(50);

  /* soft-reset sequence */
  writeReg(REG_SOFT_RST, 0xB6);
  delay(50);
  writeReg(REG_SOFT_RST, 0x00);
  delay(10);

  (void)readReg(REG_CHIP_ID);         /* verify sensor present */

  /* standby -> configure -> active */
  uint8_t pm = readReg(REG_PM) & ~0x03;
  writeReg(REG_PM, pm);
  writeReg(REG_RANGE,  0x04);         /* +/-8g  */
  writeReg(REG_BW_ODR, 0x05);         /* 128Hz  */
  writeReg(REG_PM,    0x80);          /* active mode */
  delay(30);

  tft.fillScreen(ST77XX_BLACK);
}

/* ------------------------------------------------------ */
void loop() {
  /* read raw accelerometer data */
  float ax, ay, az;
  if (!readXYZ(ax, ay, az)) return;

  /* low-pass filter (exponential moving average) */
  static float sax = 0.0f, say = 0.0f, saz = -1.0f;
  sax = sax * (1.0f - SMOOTH) + ax * SMOOTH;
  say = say * (1.0f - SMOOTH) + ay * SMOOTH;
  saz = saz * (1.0f - SMOOTH) + az * SMOOTH;

  /* normalise gravity vector */
  float mag = sqrt(sax * sax + say * say + saz * saz);
  if (mag < 0.01f) mag = 1.0f;
  float nax = sax / mag;
  float nay = say / mag;
  float naz = saz / mag;

  /*
   * Rotation angles from tilt.
   * Negative sign -> cube compensates for board tilt,
   * appearing to stay level in world-space.
   */
  float angleX = -nay * SENSITIVITY;   /* roll  (rotate around X) */
  float angleY = -nax * SENSITIVITY;   /* pitch (rotate around Y) */

  float cosX = cos(angleX), sinX = sin(angleX);
  float cosY = cos(angleY), sinY = sin(angleY);

  /* 3D -> 2D projection */
  int px[8], py[8];

  for (int i = 0; i < 8; i++) {
    float x = verts[i][0];
    float y = verts[i][1];
    float z = verts[i][2];

    /* rotate around Y axis (pitch) */
    float x1 =  x * cosY + z * sinY;
    float z1 = -x * sinY + z * cosY;
    float y1 =  y;

    /* rotate around X axis (roll) */
    float y2 =  y1 * cosX - z1 * sinX;
    float z2 =  y1 * sinX + z1 * cosX;
    float x2 =  x1;

    /* perspective projection */
    float s  = CUBE_SIZE / (z2 + PERSP_DIST);
    px[i] = SCREEN_CX + (int)(x2 * s);
    py[i] = SCREEN_CY + (int)(y2 * s);
  }

  /* draw wireframe */
  tft.fillScreen(ST77XX_BLACK);

  for (int e = 0; e < 12; e++) {
    uint8_t a = edges[e][0];
    uint8_t b = edges[e][1];
    tft.drawLine(px[a], py[a], px[b], py[b], ST77XX_CYAN);
  }

  /* centre reference dot */
  tft.fillCircle(SCREEN_CX, SCREEN_CY, 2, ST77XX_WHITE);

  delay(25);   /* ~40 FPS cap */
}
