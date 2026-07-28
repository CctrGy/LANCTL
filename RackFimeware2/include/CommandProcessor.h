#pragma once

#include <Arduino.h>
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
  String executeUnlocked(String command);
  String fanCommand(const String &command);
  String temperatureCommand(const String &command);
  String editNetwork(const String &command);
};
