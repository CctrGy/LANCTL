#include "StatusLeds.h"

#include "Config.h"

StatusLeds::StatusLeds() : pixels_(Config::NEOPIXEL_COUNT, Config::NEOPIXEL, NEO_GRB + NEO_KHZ800) {}
void StatusLeds::begin() { pixels_.begin(); pixels_.clear(); pixels_.show(); }

void StatusLeds::update(const TemperatureSnapshot &t, const ThermalController &thermal,
                        const NetworkService &network) {
  pixels_.setPixelColor(0, thermal.failsafe() ? pixels_.Color(80, 0, 0) :
                        (t.top.degraded || t.bottom.degraded ? pixels_.Color(80, 40, 0) : pixels_.Color(0, 50, 0)));
  pixels_.setPixelColor(1, thermal.fan2() ? pixels_.Color(60, 0, 60) :
                        (thermal.fan1() ? pixels_.Color(0, 0, 60) : pixels_.Color(0, 20, 0)));
  pixels_.setPixelColor(2, network.ready() ? pixels_.Color(0, 40, 0) : pixels_.Color(40, 20, 0));
  pixels_.show();
}

