#pragma once

#include <Arduino.h>

#ifndef SSH_PORT
#define SSH_PORT 22
#endif
#ifndef SSH_USERNAME
#define SSH_USERNAME "admin"
#endif
#ifndef SSH_PASSWORD
#define SSH_PASSWORD "CHANGE_ME_BEFORE_FLASHING"
#endif

namespace Config {
constexpr uint32_t ONEWIRE_TOP = PB1;
constexpr uint32_t ONEWIRE_BOTTOM = PB2;
constexpr uint8_t PROBES_PER_GROUP = 1;
constexpr uint32_t ETH_MISO = PB4;
constexpr uint32_t ETH_MOSI = PB5;
constexpr uint32_t ETH_SCLK = PB3;
constexpr uint32_t ETH_RESET = PB6;
constexpr uint32_t ETH_CS = PB7;
constexpr uint32_t ETH_INT = PB8;
constexpr uint32_t NEOPIXEL = PB10;
constexpr uint8_t NEOPIXEL_COUNT = 3;

constexpr uint32_t PIN_UNUSED = 0xFFFFFFFFUL;
constexpr uint32_t FAN1_RELAY = PA6;
constexpr uint32_t FAN2_RELAY = PA7;
constexpr bool RELAY_ACTIVE_HIGH = true;

constexpr uint32_t SENSOR_PERIOD_MS = 1000;
constexpr char DEFAULT_HOSTNAME[] = "rackmonitor";
constexpr uint32_t CONFIG_MAGIC = 0x524D4632UL;  // "RMF2"
constexpr uint16_t CONFIG_VERSION = 2;
}
