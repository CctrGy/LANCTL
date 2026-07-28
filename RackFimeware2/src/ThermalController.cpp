#include "ThermalController.h"
#include <algorithm>
#include "Config.h"

void ThermalController::writeRelay(uint32_t pin, bool on) {
  if (pin != Config::PIN_UNUSED) digitalWrite(pin, (on == Config::RELAY_ACTIVE_HIGH) ? HIGH : LOW);
}
void ThermalController::begin() {
  if (Config::FAN1_RELAY != Config::PIN_UNUSED) pinMode(Config::FAN1_RELAY, OUTPUT);
  if (Config::FAN2_RELAY != Config::PIN_UNUSED) pinMode(Config::FAN2_RELAY, OUTPUT);
  fan1_ = fan2_ = true;
  writeRelay(Config::FAN1_RELAY, true); writeRelay(Config::FAN2_RELAY, true);
}
bool ThermalController::setAutomatic(uint8_t fan, bool automatic) {
  if (fan == 1) fan1Auto_ = automatic;
  else if (fan == 2) fan2Auto_ = automatic;
  else return false;
  return true;
}
bool ThermalController::setManualValue(uint8_t fan, bool on) {
  if (fan == 1) { fan1Manual_ = on; fan1Auto_ = false; }
  else if (fan == 2) { fan2Manual_ = on; fan2Auto_ = false; }
  else return false;
  return true;
}
void ThermalController::update(const TemperatureSnapshot &t, const ThermalConfig &c) {
  failsafe_ = !t.anyUsable || t.top.mismatch || t.bottom.mismatch;
  if (t.top.validCount && t.bottom.validCount) controlTemperature_ = std::max(t.top.mean, t.bottom.mean);
  else if (t.top.validCount) controlTemperature_ = t.top.mean;
  else if (t.bottom.validCount) controlTemperature_ = t.bottom.mean;
  else controlTemperature_ = NAN;
  if (failsafe_ && c.failsafeBothOn) fan1_ = fan2_ = true;
  else {
    if (fan1Auto_) {
      if (!fan1_ && controlTemperature_ >= c.fan1OnC) fan1_ = true;
      if (fan1_ && controlTemperature_ <= c.fan1OnC - c.hysteresisC) fan1_ = false;
    } else fan1_ = fan1Manual_;
    if (fan2Auto_) {
      if (!fan2_ && controlTemperature_ >= c.fan2OnC) fan2_ = true;
      if (fan2_ && controlTemperature_ <= c.fan2OnC - c.hysteresisC) fan2_ = false;
    } else fan2_ = fan2Manual_;
  }
  writeRelay(Config::FAN1_RELAY, fan1_); writeRelay(Config::FAN2_RELAY, fan2_);
}
String ThermalController::describe() const {
  const String physical = Config::FAN1_RELAY == Config::PIN_UNUSED ? " (physical pins unassigned)" : "";
  return "Control temperature: " + (isfinite(controlTemperature_) ? String(controlTemperature_, 2) + " C" : "N/A") +
         "\r\nFAN1: " + (fan1Auto_ ? "AUTO, " : "MANUAL, ") + (fan1_ ? "1/ON" : "0/OFF") + physical +
         "\r\nFAN2: " + (fan2Auto_ ? "AUTO, " : "MANUAL, ") + (fan2_ ? "1/ON" : "0/OFF") + physical +
         "\r\nFailsafe: " + (failsafe_ ? "ACTIVE" : "normal");
}
