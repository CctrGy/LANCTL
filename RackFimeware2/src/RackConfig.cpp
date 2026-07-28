#include "RackConfig.h"

#include <EEPROM.h>
#include <IPAddress.h>
#include <cstring>
#include "Config.h"

namespace { String ipText(uint32_t value) { return IPAddress(value).toString(); } }

uint32_t ConfigManager::checksum(const RackConfiguration &config) {
  const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&config);
  uint32_t hash = 2166136261UL;
  for (size_t i = 0; i < offsetof(RackConfiguration, checksum); ++i) {
    hash = (hash ^ bytes[i]) * 16777619UL;
  }
  return hash;
}

bool ConfigManager::valid(const RackConfiguration &c) const {
  return c.magic == Config::CONFIG_MAGIC && c.version == Config::CONFIG_VERSION &&
         c.size == sizeof(RackConfiguration) && c.checksum == checksum(c) &&
         c.thermal.fan1OnC > -20 && c.thermal.fan1OnC < 100 &&
         c.thermal.fan2OnC > -20 && c.thermal.fan2OnC < 100 &&
         c.thermal.hysteresisC >= 0 && c.thermal.hysteresisC <= 20 &&
         c.thermal.mismatchC >= 0 && c.thermal.mismatchC <= 30;
}

void ConfigManager::begin() {
  EEPROM.get(0, running_);
  if (!valid(running_)) {
    running_ = RackConfiguration{};
    running_.checksum = checksum(running_);
  }
  candidate_ = running_;
}

bool ConfigManager::pending() const { return memcmp(&running_, &candidate_, sizeof(running_)) != 0; }
void ConfigManager::discard() { candidate_ = running_; }

bool ConfigManager::save() {
  candidate_.magic = Config::CONFIG_MAGIC;
  candidate_.version = Config::CONFIG_VERSION;
  candidate_.size = sizeof(RackConfiguration);
  candidate_.checksum = checksum(candidate_);
  if (!valid(candidate_)) return false;
  EEPROM.put(0, candidate_);
  running_ = candidate_;
  return true;
}

String ConfigManager::render(const RackConfiguration &c) const {
  String out = "hostname " + String(c.network.hostname) + "\r\n";
  out += c.network.dhcp ? "network dhcp\r\n" :
      "network static " + ipText(c.network.ip) + " " + ipText(c.network.mask) + " " + ipText(c.network.gateway) + "\r\n";
  out += "network dns " + ipText(c.network.dns1) + " " + ipText(c.network.dns2) + "\r\n";
  out += "temp curve [" + String(c.thermal.fan1OnC, 1) + "," +
         String(c.thermal.fan2OnC, 1) + "]";
  return out;
}

String ConfigManager::diff() const {
  if (!pending()) return "No pending changes";
  return "--- running\r\n+++ candidate\r\n- " + render(running_) + "\r\n+ " + render(candidate_);
}
