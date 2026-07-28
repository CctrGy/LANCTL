#include <Arduino.h>

#include "CommandProcessor.h"
#include "Config.h"
#include "NetworkConsole.h"
#include "NetworkService.h"
#include "RackConfig.h"
#include "StatusLeds.h"
#include "TemperatureService.h"
#include "ThermalController.h"
#include "UsbConsole.h"

ConfigManager rackConfig;
TemperatureService temperatures;
ThermalController thermal;
NetworkService network;
StatusLeds statusLeds;
CommandProcessor commands(rackConfig, temperatures, thermal, network);
UsbConsole usbConsole(commands);
NetworkConsole networkConsole(commands, network);

void setup() {
  Serial.begin(115200);
  const uint32_t waitStarted = millis();
  while (!Serial && millis() - waitStarted < 1500) {}
  Serial.println("\r\nRackMonitor Firmware 2 / STM32F411CE booting");
  Serial.printf("ENC28J60: MISO=PB4 MOSI=PB5 SCLK=PB3 CS=PB7 INT=PB8 RESET=PB6\r\n");
  Serial.printf("Sensors: TOP=PB1 BOTTOM=PB2 | NeoPixel=PB10\r\n");
  Serial.println("Relays: FAN1=PA6 FAN2=PA7 (active HIGH)");

  rackConfig.begin();
  thermal.begin();
  temperatures.begin();
  statusLeds.begin();
  usbConsole.begin();
  networkConsole.begin();

  Serial.printf("Network mode: %s\r\n", rackConfig.running().network.dhcp ? "DHCP" : "STATIC");
  if (!network.begin(rackConfig.running().network)) Serial.println("ERROR: ENC28J60 initialization or DHCP failed");
  else {
    Serial.printf("Ethernet MAC: %s\r\n", network.mac().c_str());
    Serial.printf("Ethernet IP: %s\r\n", Ethernet.localIP().toString().c_str());
    Serial.printf("SSH server: TCP/%u\r\n", SSH_PORT);
  }
}

void loop() {
  static uint32_t lastLedUpdate = 0;
  static uint32_t lastNetworkReport = 0;
  temperatures.update(rackConfig.running().thermal.mismatchC);
  thermal.update(temperatures.snapshot(), rackConfig.running().thermal);
  network.update();
  usbConsole.update();
  networkConsole.update();
  if (millis() - lastLedUpdate >= 250) {
    lastLedUpdate = millis();
    statusLeds.update(temperatures.snapshot(), thermal, network);
  }
  if (!network.ready() && millis() - lastNetworkReport >= 3000) {
    lastNetworkReport = millis();
    Serial.printf("Waiting for Ethernet: link=%s ip=%s mac=%s\r\n",
                  Ethernet.linkStatus() == LinkON ? "UP" : "DOWN",
                  Ethernet.localIP().toString().c_str(), network.mac().c_str());
  }
  delay(2);
}
