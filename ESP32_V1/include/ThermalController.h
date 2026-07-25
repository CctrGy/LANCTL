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
  String describe() const;

 private:
  bool fan1_ = false;
  bool fan2_ = false;
  bool failsafe_ = true;
  float controlTemperature_ = NAN;
  void writeRelay(uint8_t pin, bool on);
};

