#pragma once

#include <Arduino.h>
#include <DallasTemperature.h>
#include <OneWire.h>

struct ProbeReading { DeviceAddress address{}; float celsius = NAN; bool present = false; bool valid = false; };
struct TemperatureGroup { ProbeReading probes[2]{}; float mean = NAN; uint8_t validCount = 0; bool degraded = false; bool mismatch = false; };
struct TemperatureSnapshot { TemperatureGroup top{}; TemperatureGroup bottom{}; float deltaT = NAN; bool anyUsable = false; };

class TemperatureService {
 public:
  TemperatureService();
  void begin();
  void update(float mismatchLimit);
  const TemperatureSnapshot &snapshot() const { return snapshot_; }
  String describe() const;
 private:
  OneWire topWire_, bottomWire_;
  DallasTemperature topSensors_, bottomSensors_;
  TemperatureSnapshot snapshot_{};
  uint32_t lastRead_ = 0;
  void readGroup(DallasTemperature &bus, TemperatureGroup &group, float mismatchLimit);
};
