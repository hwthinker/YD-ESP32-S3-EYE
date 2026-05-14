#include <Arduino.h>
#line 1 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\09-i2c-scanner\\09-i2c-scanner.ino"
/*
 * 09-i2c-scanner.ino
 * Scan semua alamat I2C (0x01-0x7F) dan tampilkan hasilnya ke Serial.
 * Gunakan ini untuk mendeteksi apakah ada IMU/sensor I2C terpasang.
 *
 * Board : YD-ESP32-S3-EYE
 * SDA   : GPIO4
 * SCL   : GPIO5
 * Baud  : 115200
 */

#include <Wire.h>

#define SDA_PIN  4
#define SCL_PIN  5

#line 17 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\09-i2c-scanner\\09-i2c-scanner.ino"
void setup();
#line 32 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\09-i2c-scanner\\09-i2c-scanner.ino"
void loop();
#line 38 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\09-i2c-scanner\\09-i2c-scanner.ino"
void scanI2C();
#line 68 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\09-i2c-scanner\\09-i2c-scanner.ino"
void printKnownDevice(uint8_t addr);
#line 17 "C:\\Users\\hardware\\Documents\\REPO-Github\\YD-ESP32-S3-EYE\\source-code-arduino\\09-i2c-scanner\\09-i2c-scanner.ino"
void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);

    Serial.println("\n=============================");
    Serial.println("   I2C Scanner - ESP32-S3");
    Serial.println("=============================");
    Serial.printf("SDA = GPIO%d | SCL = GPIO%d\n\n", SDA_PIN, SCL_PIN);

    Wire.begin(SDA_PIN, SCL_PIN);
    Wire.setClock(100000);  // 100kHz standard mode

    scanI2C();
}

void loop() {
    Serial.println("\n[Scan ulang dalam 5 detik...]\n");
    delay(5000);
    scanI2C();
}

void scanI2C() {
    Serial.println("Scanning I2C bus...");
    Serial.println("-----------------------------");

    int found = 0;

    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        uint8_t err = Wire.endTransmission();

        if (err == 0) {
            Serial.printf("  [FOUND] Addr = 0x%02X (%3d)", addr, addr);
            printKnownDevice(addr);
            Serial.println();
            found++;
        } else if (err == 4) {
            Serial.printf("  [ERROR] Addr = 0x%02X - unknown error\n", addr);
        }
    }

    Serial.println("-----------------------------");
    if (found == 0) {
        Serial.println("  Tidak ada perangkat I2C ditemukan!");
        Serial.println("  Cek koneksi / tegangan / pull-up resistor.");
    } else {
        Serial.printf("  Total ditemukan: %d perangkat\n", found);
    }
    Serial.println("=============================\n");
}

void printKnownDevice(uint8_t addr) {
    switch (addr) {
        // Accelerometer / IMU
        case 0x12: Serial.print("  <-- QMA7981 / QMA6100P (Accel)");    break;
        case 0x68: Serial.print("  <-- MPU6050 / MPU6500 / ICM42688"); break;
        case 0x69: Serial.print("  <-- MPU6050 (AD0=1) / ICM42688");   break;
        case 0x18: Serial.print("  <-- LIS3DH / LIS2DH (Accel)");      break;
        case 0x19: Serial.print("  <-- LIS3DH (SA0=1)");               break;
        case 0x1C: Serial.print("  <-- MMA8452Q / FXOS8700 (Accel)");  break;
        case 0x1D: Serial.print("  <-- MMA8452Q (SA0=1)");             break;
        case 0x6A: Serial.print("  <-- LSM6DS3 / LSM6DSL (IMU)");      break;
        case 0x6B: Serial.print("  <-- LSM6DS3 (SA0=1)");              break;
        case 0x1E: Serial.print("  <-- HMC5883L / LSM303 (Mag)");      break;
        case 0x0E: Serial.print("  <-- MAG3110 (Magnetometer)");       break;

        // OLED / LCD
        case 0x3C: Serial.print("  <-- SSD1306 / SH1106 OLED");        break;
        case 0x3D: Serial.print("  <-- SSD1306 (SA0=1)");              break;

        // Environment
        case 0x76: Serial.print("  <-- BME280 / BMP280");              break;
        case 0x77: Serial.print("  <-- BME280 (SDO=1) / BMP180");      break;
        case 0x40: Serial.print("  <-- HTU21D / SHT20 / INA219");      break;
        case 0x44: Serial.print("  <-- SHT31");                        break;

        // Other
        case 0x50: Serial.print("  <-- EEPROM AT24Cxx");               break;
        case 0x70: Serial.print("  <-- TCA9548A Multiplexer");         break;
        default:   /* unknown device, no label */                       break;
    }
}

