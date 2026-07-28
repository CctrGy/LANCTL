#pragma once

#include <Adafruit_NeoPixel.h>
#include "NetworkService.h"
#include "TemperatureService.h"
#include "ThermalController.h"

class StatusLeds {
 public:
  StatusLeds();
  void begin();
  void update(const TemperatureSnapshot &, const ThermalController &, const NetworkService &);
 private:
  Adafruit_NeoPixel pixels_;
};
