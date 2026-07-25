#pragma once

#include <Adafruit_NeoPixel.h>

#include "NetworkService.h"
#include "TemperatureService.h"
#include "ThermalController.h"

class StatusLeds {
 public:
  StatusLeds();
  void begin();
  void update(const TemperatureSnapshot &temperature, const ThermalController &thermal,
              const NetworkService &network);

 private:
  Adafruit_NeoPixel pixels_;
};

