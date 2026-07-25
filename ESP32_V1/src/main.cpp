#include <Arduino.h>
#include <LittleFS.h>
#include <WiFi.h>

#include "CommandProcessor.h"
#include "Config.h"
#include "NetworkService.h"
#include "RackConfig.h"
#include "StatusLeds.h"
#include "TemperatureService.h"
#include "ThermalController.h"
#include "UsbConsole.h"

void startSshServer(CommandProcessor &commands);

ConfigManager rackConfig;
TemperatureService temperatures;
ThermalController thermal;
NetworkService network;
StatusLeds statusLeds;
CommandProcessor commands(rackConfig, temperatures, thermal, network);
UsbConsole usbConsole(commands);
bool sshStarted = false;

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("RackMonitor Hardware V1 booting");

  WiFi.mode(WIFI_OFF);
  rackConfig.begin();
  thermal.begin();
  temperatures.begin();
  statusLeds.begin();
  for (uint8_t pin : Config::BUTTONS) pinMode(pin, INPUT_PULLUP);

  if (!LittleFS.begin(true)) Serial.println("ERROR: LittleFS mount failed");
  Serial.println("Initializing ENC28J60:");
  Serial.printf("  SPI: HOST=%u MOSI=%u MISO=%u SCLK=%u CS=%u INT=%u RESET=%u\n",
                Config::ETH_SPI_HOST,
                Config::ETH_MOSI, Config::ETH_MISO, Config::ETH_SCLK,
                Config::ETH_CS, Config::ETH_INT, Config::ETH_RESET);
  Serial.printf("  Network mode: %s\n", rackConfig.running().network.dhcp ? "DHCP" : "STATIC");
  if (!network.begin(rackConfig.running().network)) {
    Serial.println("ERROR: ENC28J60 initialization failed");
  } else {
    Serial.printf("  Ethernet MAC: %s\n", network.mac().c_str());
    Serial.println("ENC28J60 initialized; waiting for link and IP");
  }
  usbConsole.begin();
}

void loop() {
  static uint32_t lastLedUpdate = 0;
  static uint32_t lastNetworkReport = 0;
  static bool previousLink = false;
  temperatures.update(rackConfig.running().thermal.mismatchC);
  thermal.update(temperatures.snapshot(), rackConfig.running().thermal);
  network.update();
  usbConsole.update();
  const bool currentLink = ETH.linkUp();
  if (currentLink != previousLink) {
    Serial.printf("Ethernet link: %s\n", currentLink ? "UP" : "DOWN");
    previousLink = currentLink;
  }
  if (millis() - lastLedUpdate >= 250) {
    lastLedUpdate = millis();
    statusLeds.update(temperatures.snapshot(), thermal, network);
  }

  if (!sshStarted && network.ready()) {
    Serial.println("Ethernet configuration ready:");
    Serial.printf("  MAC:     %s\n", network.mac().c_str());
    Serial.printf("  IP:      %s\n", ETH.localIP().toString().c_str());
    Serial.printf("  Mask:    %s\n", ETH.subnetMask().toString().c_str());
    Serial.printf("  Gateway: %s\n", ETH.gatewayIP().toString().c_str());
    Serial.printf("  DNS1:    %s\n", ETH.dnsIP(0).toString().c_str());
    startSshServer(commands);
    sshStarted = true;
  } else if (!sshStarted && millis() - lastNetworkReport >= 2000) {
    lastNetworkReport = millis();
    Serial.printf("Waiting for Ethernet: link=%s ip=%s mac=%s\n",
                  ETH.linkUp() ? "UP" : "DOWN", ETH.localIP().toString().c_str(),
                  network.mac().c_str());
  }
  delay(10);
}
