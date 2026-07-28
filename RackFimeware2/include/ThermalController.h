#pragma once

#include <Arduino.h>
#include "RackConfig.h"
#include "TemperatureService.h"

class ThermalController {
 public:
  void begin();
  void update(const TemperatureSnapshot &temperatures, const ThermalConfig &config);
  bool fan1() const { return fan1_; }
  bool fan2() const { return fan2_; }
  bool failsafe() const { return failsafe_; }
  float controlTemperature() const { return controlTemperature_; }
  bool setAutomatic(uint8_t fan, bool automatic);
  bool setManualValue(uint8_t fan, bool on);
  String describe() const;
 private:
  bool fan1_ = false, fan2_ = false, failsafe_ = true;
  bool fan1Auto_ = true, fan2Auto_ = true;
  bool fan1Manual_ = false, fan2Manual_ = false;
  float controlTemperature_ = NAN;
  void writeRelay(uint32_t pin, bool on);
};
