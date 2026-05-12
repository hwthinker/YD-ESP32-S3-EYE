/*
 * 04-test-sdcard.ino
 * Mengakses microSD Card pada ESP32-S3-EYE menggunakan mode SDMMC (1-bit).
 * 
 * Board: ESP32-S3-EYE (Official) atau varian yang kompatibel.
 * Pinout SDMMC pada EYE:
 * - CLK: GPIO 39
 * - CMD: GPIO 38
 * - D0 : GPIO 40
 */

#include "FS.h"
#include "SD_MMC.h"

void listDir(fs::FS &fs, const char * dirname, uint8_t levels){
    Serial.printf("Listing directory: %s\n", dirname);

    File root = fs.open(dirname);
    if(!root){
        Serial.println("Failed to open directory");
        return;
    }
    if(!root.isDirectory()){
        Serial.println("Not a directory");
        return;
    }

    File file = root.openNextFile();
    while(file){
        if(file.isDirectory()){
            Serial.print("  DIR : ");
            Serial.println(file.name());
            if(levels){
                listDir(fs, file.path(), levels -1);
            }
        } else {
            Serial.print("  FILE: ");
            Serial.print(file.name());
            Serial.print("  SIZE: ");
            Serial.println(file.size());
        }
        file = root.openNextFile();
    }
}

void writeFile(fs::FS &fs, const char * path, const char * message){
    Serial.printf("Writing file: %s\n", path);

    File file = fs.open(path, FILE_WRITE);
    if(!file){
        Serial.println("Failed to open file for writing");
        return;
    }
    if(file.print(message)){
        Serial.println("File written");
    } else {
        Serial.println("Write failed");
    }
    file.close();
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n--- ESP32-S3-EYE SD Card Test ---");

    // Konfigurasi Pin SDMMC untuk ESP32-S3-EYE
    // setPins(clk, cmd, d0)
    if(!SD_MMC.setPins(39, 38, 40)){
        Serial.println("Pin configuration failed!");
        return;
    }

    // Inisialisasi SD_MMC dalam mode 1-bit (true)
    // Board EYE hanya mendukung mode 1-bit untuk SD card.
    if(!SD_MMC.begin("/sdcard", true)){
        Serial.println("Card Mount Failed. Pastikan SD Card sudah terpasang dan berformat FAT32.");
        return;
    }

    uint8_t cardType = SD_MMC.cardType();
    if(cardType == CARD_NONE){
        Serial.println("No SD card attached");
        return;
    }

    Serial.print("SD Card Type: ");
    if(cardType == CARD_MMC) Serial.println("MMC");
    else if(cardType == CARD_SD) Serial.println("SDSC");
    else if(cardType == CARD_SDHC) Serial.println("SDHC");
    else Serial.println("UNKNOWN");

    uint64_t cardSize = SD_MMC.cardSize() / (1024 * 1024);
    Serial.printf("SD Card Size: %lluMB\n", cardSize);

    // List isi direktori root
    listDir(SD_MMC, "/", 0);

    // Tulis file hello.txt
    writeFile(SD_MMC, "/hello.txt", "hello from esp32-s3 eye-OK\n");

    Serial.println("\nSelesai! Anda bisa mencabut SD card dan mengecek file 'hello.txt' di komputer.");
}

void loop() {
    // Kosong
}
