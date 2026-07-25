#include "CommandProcessor.h"

#include <cstring>

namespace {
String wordAt(const String &text, uint8_t wanted) {
  uint8_t current = 0;
  int start = 0;
  while (start < text.length()) {
    while (start < text.length() && text[start] == ' ') ++start;
    int end = text.indexOf(' ', start);
    if (end < 0) end = text.length();
    if (current++ == wanted) return text.substring(start, end);
    start = end + 1;
  }
  return "";
}

bool parseFloatStrict(const String &text, float &value) {
  if (!text.length()) return false;
  char *end = nullptr;
  value = strtof(text.c_str(), &end);
  return end && *end == '\0' && isfinite(value);
}
}

CommandProcessor::CommandProcessor(ConfigManager &config, TemperatureService &temperatures,
                                   ThermalController &thermal, NetworkService &network)
    : config_(config), temperatures_(temperatures), thermal_(thermal), network_(network),
      mutex_(xSemaphoreCreateMutex()) {}

String CommandProcessor::execute(String command) {
  if (mutex_) xSemaphoreTake(mutex_, portMAX_DELAY);
  String result = executeUnlocked(command);
  if (mutex_) xSemaphoreGive(mutex_);
  return result;
}

String CommandProcessor::executeUnlocked(String command) {
  command.trim();
  command.toLowerCase();
  if (!command.length()) return "";
  if (command == "help" || command == "?") return
      "show [system|temperature|fan|network|running-config|startup-config]\r\n"
      "configure terminal\r\n"
      "temperature fan1-on <C>\r\n"
      "temperature fan2-on <C>\r\n"
      "temperature hysteresis <C>\r\n"
      "temperature mismatch <C>\r\n"
      "network dhcp\r\n"
      "network static <ip> <mask> <gateway>\r\n"
      "network dns <dns1> [dns2]\r\n"
      "hostname <name>\r\n"
      "config [pending|diff|discard|save]\r\n"
      "reboot | exit | logout | quit | help";
  if (command == "show") return show("show system");
  if (command.startsWith("show ")) return show(command);
  if (command == "configure terminal") return "Candidate configuration mode. Changes require 'config save'.";
  if (command.startsWith("temperature ")) return editTemperature(command);
  if (command.startsWith("network ")) return editNetwork(command);
  if (command.startsWith("hostname ")) {
    const String hostname = wordAt(command, 1);
    if (!hostname.length() || hostname.length() >= sizeof(config_.edit().network.hostname)) return "ERR: hostname length must be 1..31";
    hostname.toCharArray(config_.edit().network.hostname, sizeof(config_.edit().network.hostname));
    return "OK: candidate changed";
  }
  if (command == "config pending") return config_.pending() ? "Pending changes: yes" : "Pending changes: no";
  if (command == "config diff") return config_.diff();
  if (command == "config discard") { config_.discard(); return "OK: candidate discarded"; }
  if (command == "config save") return config_.save() ? "OK: startup and running config updated; reboot required for network changes" : "ERR: invalid configuration or NVS write failure";
  if (command == "reboot") { delay(100); ESP.restart(); return "Rebooting"; }
  return "ERR: unknown command; use help";
}

String CommandProcessor::show(const String &command) {
  const String section = wordAt(command, 1);
  if (section == "temperature" || section == "temp") return temperatures_.describe();
  if (section == "fan") return thermal_.describe();
  if (section == "network") return network_.describe();
  if (section == "running-config") return config_.render(config_.running());
  if (section == "startup-config") return config_.render(config_.running());
  if (section == "system" || !section.length()) {
    return "RackMonitor Hardware V1\r\nUptime: " + String(millis() / 1000) + " s\r\nFree heap: " +
           String(ESP.getFreeHeap()) + " bytes\r\nConfig pending: " + (config_.pending() ? "yes" : "no") +
           "\r\n" + network_.describe() + "\r\n" + thermal_.describe();
  }
  return "ERR: unknown show section";
}

String CommandProcessor::editTemperature(const String &command) {
  const String property = wordAt(command, 1);
  float value;
  if (!parseFloatStrict(wordAt(command, 2), value)) return "ERR: numeric temperature required";
  if (property == "fan1-on" && value > -20 && value < 100) config_.edit().thermal.fan1OnC = value;
  else if (property == "fan2-on" && value > -20 && value < 100) config_.edit().thermal.fan2OnC = value;
  else if (property == "hysteresis" && value >= 0 && value <= 20) config_.edit().thermal.hysteresisC = value;
  else if (property == "mismatch" && value >= 0 && value <= 30) config_.edit().thermal.mismatchC = value;
  else return "ERR: invalid property or value";
  return "OK: candidate changed";
}

String CommandProcessor::editNetwork(const String &command) {
  const String action = wordAt(command, 1);
  if (action == "dhcp") { config_.edit().network.dhcp = true; return "OK: candidate changed"; }
  if (action == "static") {
    IPAddress ip, mask, gateway;
    if (!ip.fromString(wordAt(command, 2)) || !mask.fromString(wordAt(command, 3)) || !gateway.fromString(wordAt(command, 4)))
      return "ERR: usage: network static <ip> <mask> <gateway>";
    auto &n = config_.edit().network;
    n.dhcp = false; n.ip = static_cast<uint32_t>(ip); n.mask = static_cast<uint32_t>(mask); n.gateway = static_cast<uint32_t>(gateway);
    return "OK: candidate changed";
  }
  if (action == "dns") {
    IPAddress dns1, dns2;
    if (!dns1.fromString(wordAt(command, 2))) return "ERR: usage: network dns <dns1> [dns2]";
    dns2.fromString(wordAt(command, 3));
    config_.edit().network.dns1 = static_cast<uint32_t>(dns1);
    config_.edit().network.dns2 = static_cast<uint32_t>(dns2);
    return "OK: candidate changed";
  }
  return "ERR: usage: network <dhcp|static|dns>";
}
