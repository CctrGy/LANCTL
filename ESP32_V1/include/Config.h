#pragma once

#include <Arduino.h>

#ifndef SSH_USERNAME
#define SSH_USERNAME "admin"
#endif
#ifndef SSH_PASSWORD
#define SSH_PASSWORD "admin"
#endif
#ifndef SSH_PORT
#define SSH_PORT 22
#endif

namespace Config {
constexpr uint8_t ONEWIRE_TOP = 4;
constexpr uint8_t ONEWIRE_BOTTOM = 5;
constexpr uint8_t ETH_MISO = 6;
constexpr uint8_t ETH_MOSI = 7;
constexpr uint8_t ETH_SCLK = 15;
constexpr uint8_t ETH_CS = 16;
constexpr uint8_t ETH_INT = 17;
constexpr uint8_t ETH_RESET = 10;
constexpr uint8_t FAN1_RELAY = 11;
constexpr uint8_t FAN2_RELAY = 12;
constexpr uint8_t NEOPIXEL = 13;
constexpr uint8_t NEOPIXEL_COUNT = 3;
constexpr uint8_t BUTTONS[] = {1, 2, 40, 41, 42};
constexpr bool RELAY_ACTIVE_HIGH = true;
constexpr uint8_t ETH_SPI_HOST = 1;
constexpr uint8_t ETH_SPI_MHZ = 8;
constexpr uint32_t SENSOR_PERIOD_MS = 1000;
constexpr char DEFAULT_HOSTNAME[] = "rackmonitor";
constexpr char PREF_NAMESPACE[] = "rackmon";
}
