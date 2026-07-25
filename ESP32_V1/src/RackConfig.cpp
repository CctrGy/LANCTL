#include "RackConfig.h"

#include <IPAddress.h>
#include <cstring>

#include "Config.h"

namespace {
String ipText(uint32_t value) { return IPAddress(value).toString(); }
}

void ConfigManager::begin() {
  Preferences prefs;
  prefs.begin(Config::PREF_NAMESPACE, true);
  if (prefs.getBytesLength("startup") == sizeof(running_)) {
    prefs.getBytes("startup", &running_, sizeof(running_));
    if (!valid(running_)) running_ = RackConfiguration{};
  }
  prefs.end();
  candidate_ = running_;
}

bool ConfigManager::valid(const RackConfiguration &c) const {
  return c.version == 1 && c.thermal.fan1OnC > -20 && c.thermal.fan1OnC < 100 &&
         c.thermal.fan2OnC > -20 && c.thermal.fan2OnC < 100 &&
         c.thermal.hysteresisC >= 0 && c.thermal.hysteresisC <= 20 &&
         c.thermal.mismatchC >= 0 && c.thermal.mismatchC <= 30;
}

bool ConfigManager::pending() const { return memcmp(&running_, &candidate_, sizeof(running_)) != 0; }

void ConfigManager::discard() { candidate_ = running_; }

bool ConfigManager::save() {
  if (!valid(candidate_)) return false;
  Preferences prefs;
  if (!prefs.begin(Config::PREF_NAMESPACE, false)) return false;
  const bool ok = prefs.putBytes("startup", &candidate_, sizeof(candidate_)) == sizeof(candidate_);
  prefs.end();
  if (ok) running_ = candidate_;
  return ok;
}

String ConfigManager::render(const RackConfiguration &c) const {
  String out;
  out += "hostname " + String(c.network.hostname) + "\r\n";
  out += c.network.dhcp ? "network dhcp\r\n" :
      "network static " + ipText(c.network.ip) + " " + ipText(c.network.mask) + " " + ipText(c.network.gateway) + "\r\n";
  out += "network dns " + ipText(c.network.dns1) + " " + ipText(c.network.dns2) + "\r\n";
  out += "temperature fan1-on " + String(c.thermal.fan1OnC, 1) + "\r\n";
  out += "temperature fan2-on " + String(c.thermal.fan2OnC, 1) + "\r\n";
  out += "temperature hysteresis " + String(c.thermal.hysteresisC, 1) + "\r\n";
  out += "temperature mismatch " + String(c.thermal.mismatchC, 1);
  return out;
}

String ConfigManager::diff() const {
  if (!pending()) return "No pending changes";
  return "--- running\r\n+++ candidate\r\n- " + render(running_) + "\r\n+ " + render(candidate_);
}

