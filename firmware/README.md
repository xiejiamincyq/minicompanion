# Devotchi Firmware

ESP32-S3 firmware for the Devotchi physical device. Written in C using ESP-IDF.

This is built separately from the Node.js packages. Not part of the pnpm workspace.

## Target hardware

- **MCU:** ESP32-S3-MINI-1 (dual-core 240MHz, WiFi + BLE 5.0, integrated PCB antenna)
- **Display:** HS20HS072RX 2.0" 320x240 color TFT LCD (ST7789, SPI, IPS)
- **Input:** 3 front buttons (approve/reject/action) — any button press wakes from deep sleep
- **Output:** status LED (PWM), vibration motor (GPIO via MOSFET)
- **Power:** LiPo battery, TP4056 charger, ME6211 3.3V LDO, USB-C charging
- **Communication:** WiFi (WebSocket to server) + BLE (to phone PWA)

## Build system

Will use ESP-IDF (not Arduino framework) with CMake. PlatformIO may be used as an alternative build tool.

## Firmware responsibilities

1. Connect to WiFi and establish WebSocket connection to server
2. Register as a consumer with token
3. Receive protocol messages and render Tamagotchi character on TFT LCD
4. Handle button presses and send responses back via WebSocket
5. Manage power states (active, idle, light sleep, deep sleep)
6. Drive vibration motor and LED for notifications
7. Optionally connect via BLE to phone PWA as a bridge
8. Read battery level via ADC and report via device info

## Status

Not yet started. PCB design is complete and boards have been ordered from JLCPCB. Firmware development will begin when the PCBs arrive.
