#include "TemperatureService.h"
#include <algorithm>
#include "Config.h"

TemperatureService::TemperatureService()
    : topWire_(Config::ONEWIRE_TOP), bottomWire_(Config::ONEWIRE_BOTTOM),
      topSensors_(&topWire_), bottomSensors_(&bottomWire_) {}

void TemperatureService::begin() {
  topSensors_.begin(); bottomSensors_.begin();
  topSensors_.setResolution(11); bottomSensors_.setResolution(11);
  topSensors_.setWaitForConversion(false); bottomSensors_.setWaitForConversion(false);
  topSensors_.requestTemperatures(); bottomSensors_.requestTemperatures();
  lastRead_ = millis();
}

void TemperatureService::readGroup(DallasTemperature &bus, TemperatureGroup &group, float mismatchLimit) {
  group = TemperatureGroup{};
  const uint8_t count = std::min<uint8_t>(bus.getDeviceCount(), Config::PROBES_PER_GROUP);
  for (uint8_t i = 0; i < count; ++i) {
    auto &probe = group.probes[i];
    probe.present = bus.getAddress(probe.address, i);
    if (!probe.present) continue;
    probe.celsius = bus.getTempC(probe.address);
    probe.valid = probe.celsius != DEVICE_DISCONNECTED_C && isfinite(probe.celsius) && probe.celsius >= -55 && probe.celsius <= 125;
    if (probe.valid) { group.mean = group.validCount ? group.mean + probe.celsius : probe.celsius; ++group.validCount; }
  }
  if (group.validCount) group.mean /= group.validCount;
  group.degraded = group.validCount > 0 && group.validCount < Config::PROBES_PER_GROUP;
  group.mismatch = Config::PROBES_PER_GROUP > 1 && group.validCount == 2 &&
                   fabsf(group.probes[0].celsius - group.probes[1].celsius) > mismatchLimit;
}

void TemperatureService::update(float mismatchLimit) {
  if (millis() - lastRead_ < Config::SENSOR_PERIOD_MS) return;
  readGroup(topSensors_, snapshot_.top, mismatchLimit);
  readGroup(bottomSensors_, snapshot_.bottom, mismatchLimit);
  snapshot_.anyUsable = snapshot_.top.validCount || snapshot_.bottom.validCount;
  snapshot_.deltaT = snapshot_.top.validCount && snapshot_.bottom.validCount ? snapshot_.top.mean - snapshot_.bottom.mean : NAN;
  topSensors_.requestTemperatures(); bottomSensors_.requestTemperatures();
  lastRead_ = millis();
}

String TemperatureService::describe() const {
  auto text = [](const char *name, const TemperatureGroup &g) {
    String s = String(name) + ": mean=" + (g.validCount ? String(g.mean, 2) + " C" : "N/A");
    s += ", A=" + (g.probes[0].valid ? String(g.probes[0].celsius, 2) + " C" : "FAULT");
    if (Config::PROBES_PER_GROUP > 1)
      s += ", B=" + (g.probes[1].valid ? String(g.probes[1].celsius, 2) + " C" : "FAULT");
    if (g.degraded) s += ", DEGRADED"; if (g.mismatch) s += ", MISMATCH";
    return s;
  };
  String out = text("TOP", snapshot_.top) + "\r\n" + text("BOTTOM", snapshot_.bottom);
  out += "\r\nDeltaT: " + (isfinite(snapshot_.deltaT) ? String(snapshot_.deltaT, 2) + " C" : "N/A");
  return out;
}
