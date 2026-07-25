#pragma once

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

#include "NetworkService.h"
#include "RackConfig.h"
#include "TemperatureService.h"
#include "ThermalController.h"

class CommandProcessor {
 public:
  CommandProcessor(ConfigManager &config, TemperatureService &temperatures,
                   ThermalController &thermal, NetworkService &network);
  String execute(String command);

 private:
  ConfigManager &config_;
  TemperatureService &temperatures_;
  ThermalController &thermal_;
  NetworkService &network_;
  SemaphoreHandle_t mutex_ = nullptr;
  String executeUnlocked(String command);
  String show(const String &command);
  String editTemperature(const String &command);
  String editNetwork(const String &command);
};
