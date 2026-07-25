#pragma once

#include <Arduino.h>
#include <Preferences.h>

struct NetworkConfig {
  bool dhcp = true;
  uint32_t ip = 0;
  uint32_t mask = 0;
  uint32_t gateway = 0;
  uint32_t dns1 = 0;
  uint32_t dns2 = 0;
  char hostname[32] = "rackmonitor";
};

struct ThermalConfig {
  float fan1OnC = 28.0F;
  float fan2OnC = 32.0F;
  float hysteresisC = 2.0F;
  float mismatchC = 3.0F;
  bool failsafeBothOn = true;
};

struct RackConfiguration {
  uint32_t version = 1;
  NetworkConfig network{};
  ThermalConfig thermal{};
};

class ConfigManager {
 public:
  void begin();
  const RackConfiguration &running() const { return running_; }
  const RackConfiguration &candidate() const { return candidate_; }
  RackConfiguration &edit() { return candidate_; }
  bool pending() const;
  void discard();
  bool save();
  String diff() const;
  String render(const RackConfiguration &config) const;

 private:
  RackConfiguration running_{};
  RackConfiguration candidate_{};
  bool valid(const RackConfiguration &config) const;
};

