#pragma once

#include <Arduino.h>
#include <ESP32-ENC28J60.h>

#include "RackConfig.h"

class NetworkService {
 public:
  bool begin(const NetworkConfig &config);
  void update();
  bool ready() const;
  String describe() const;
  String mac() const;

 private:
  uint8_t mac_[6]{};
  bool started_ = false;
};

