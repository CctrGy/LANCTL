#include "ThermalController.h"

#include "Config.h"

void ThermalController::writeRelay(uint8_t pin, bool on) {
  digitalWrite(pin, (on == Config::RELAY_ACTIVE_HIGH) ? HIGH : LOW);
}

void ThermalController::begin() {
  pinMode(Config::FAN1_RELAY, OUTPUT);
  pinMode(Config::FAN2_RELAY, OUTPUT);
  fan1_ = fan2_ = true;
  writeRelay(Config::FAN1_RELAY, true);
  writeRelay(Config::FAN2_RELAY, true);
}

void ThermalController::update(const TemperatureSnapshot &t, const ThermalConfig &c) {
  failsafe_ = !t.anyUsable || t.top.mismatch || t.bottom.mismatch;
  if (t.top.validCount && t.bottom.validCount) controlTemperature_ = max(t.top.mean, t.bottom.mean);
  else if (t.top.validCount) controlTemperature_ = t.top.mean;
  else if (t.bottom.validCount) controlTemperature_ = t.bottom.mean;
  else controlTemperature_ = NAN;

  if (failsafe_ && c.failsafeBothOn) {
    fan1_ = fan2_ = true;
  } else {
    if (!fan1_ && controlTemperature_ >= c.fan1OnC) fan1_ = true;
    if (fan1_ && controlTemperature_ <= c.fan1OnC - c.hysteresisC) fan1_ = false;
    if (!fan2_ && controlTemperature_ >= c.fan2OnC) fan2_ = true;
    if (fan2_ && controlTemperature_ <= c.fan2OnC - c.hysteresisC) fan2_ = false;
  }
  writeRelay(Config::FAN1_RELAY, fan1_);
  writeRelay(Config::FAN2_RELAY, fan2_);
}

String ThermalController::describe() const {
  return "Control temperature: " + (isfinite(controlTemperature_) ? String(controlTemperature_, 2) + " C" : "N/A") +
         "\r\nFAN1 relay: " + (fan1_ ? "ON" : "OFF") +
         "\r\nFAN2 relay: " + (fan2_ ? "ON" : "OFF") +
         "\r\nFailsafe: " + (failsafe_ ? "ACTIVE" : "normal");
}

