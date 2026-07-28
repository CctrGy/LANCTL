#include "NetworkService.h"

#include <SPI.h>
#include "Config.h"

bool NetworkService::begin(const NetworkConfig &config) {
  pinMode(Config::ETH_RESET, OUTPUT);
  digitalWrite(Config::ETH_RESET, LOW);
  delay(20);
  digitalWrite(Config::ETH_RESET, HIGH);
  delay(150);

  SPI.setMISO(Config::ETH_MISO);
  SPI.setMOSI(Config::ETH_MOSI);
  SPI.setSCLK(Config::ETH_SCLK);
  Ethernet.init(Config::ETH_CS);

  const uint32_t uid0 = HAL_GetUIDw0();
  const uint32_t uid1 = HAL_GetUIDw1();
  mac_[0] = 0x02;
  mac_[1] = static_cast<byte>(uid0 >> 24);
  mac_[2] = static_cast<byte>(uid0 >> 16);
  mac_[3] = static_cast<byte>(uid0 >> 8);
  mac_[4] = static_cast<byte>(uid1 >> 8);
  mac_[5] = static_cast<byte>(uid1);

  if (config.dhcp) {
    started_ = Ethernet.begin(mac_, 10000, 2000) != 0;
  } else {
    Ethernet.begin(mac_, IPAddress(config.ip), IPAddress(config.dns1),
                   IPAddress(config.gateway), IPAddress(config.mask));
    started_ = static_cast<uint32_t>(Ethernet.localIP()) != 0;
  }
  if (started_) consoleServer_.begin();
  return started_;
}

void NetworkService::update() { if (started_) Ethernet.maintain(); }
bool NetworkService::ready() const {
  return started_ && Ethernet.linkStatus() == LinkON && static_cast<uint32_t>(Ethernet.localIP()) != 0;
}
String NetworkService::mac() const {
  char text[18];
  snprintf(text, sizeof(text), "%02X:%02X:%02X:%02X:%02X:%02X", mac_[0], mac_[1], mac_[2], mac_[3], mac_[4], mac_[5]);
  return String(text);
}
String NetworkService::describe() const {
  return "Link: " + String(Ethernet.linkStatus() == LinkON ? "UP" : "DOWN") +
         "\r\nMAC: " + mac() + "\r\nIP: " + Ethernet.localIP().toString() +
         "\r\nMask: " + Ethernet.subnetMask().toString() +
         "\r\nGateway: " + Ethernet.gatewayIP().toString() +
         "\r\nDNS1: " + Ethernet.dnsServerIP().toString();
}
