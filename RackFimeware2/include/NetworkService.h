#pragma once

#include <Arduino.h>
#include <EthernetENC.h>

#include "RackConfig.h"

class NetworkService {
 public:
  bool begin(const NetworkConfig &config);
  void update();
  bool ready() const;
  String describe() const;
  String mac() const;
  EthernetServer &consoleServer() { return consoleServer_; }

 private:
  byte mac_[6]{};
  bool started_ = false;
  EthernetServer consoleServer_{SSH_PORT};
};
