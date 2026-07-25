#include "NetworkService.h"

#include <esp_system.h>

#include "Config.h"

bool NetworkService::begin(const NetworkConfig &config) {
  pinMode(Config::ETH_RESET, OUTPUT);
  digitalWrite(Config::ETH_RESET, LOW);
  delay(10);
  digitalWrite(Config::ETH_RESET, HIGH);
  delay(100);
  started_ = ETH.begin(Config::ETH_MISO, Config::ETH_MOSI, Config::ETH_SCLK,
                       Config::ETH_CS, Config::ETH_INT, Config::ETH_SPI_MHZ,
                       Config::ETH_SPI_HOST, false);
  if (started_) {
    ETH.setHostname(config.hostname);
    ETH.macAddress(mac_);
  }
  if (started_ && !config.dhcp) {
    ETH.config(IPAddress(config.ip), IPAddress(config.gateway), IPAddress(config.mask),
               IPAddress(config.dns1), IPAddress(config.dns2));
  }
  return started_;
}

void NetworkService::update() {}
bool NetworkService::ready() const { return started_ && ETH.linkUp() && static_cast<uint32_t>(ETH.localIP()) != 0; }
String NetworkService::mac() const {
  char text[18];
  snprintf(text, sizeof(text), "%02X:%02X:%02X:%02X:%02X:%02X",
           mac_[0], mac_[1], mac_[2], mac_[3], mac_[4], mac_[5]);
  return String(text);
}

String NetworkService::describe() const {
  return "Link: " + String(ETH.linkUp() ? "UP" : "DOWN") +
         "\r\nMAC: " + mac() + "\r\nIP: " + ETH.localIP().toString() +
         "\r\nMask: " + ETH.subnetMask().toString() +
         "\r\nGateway: " + ETH.gatewayIP().toString() +
         "\r\nDNS1: " + ETH.dnsIP(0).toString();
}
