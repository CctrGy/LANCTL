#include "CommandProcessor.h"

#include <cstring>

namespace {
String wordAt(const String &text, uint8_t wanted) {
  uint8_t current = 0;
  int start = 0;
  while (start < static_cast<int>(text.length())) {
    while (start < static_cast<int>(text.length()) && text[start] == ' ') ++start;
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
    : config_(config), temperatures_(temperatures), thermal_(thermal), network_(network) {}

String CommandProcessor::execute(String command) { return executeUnlocked(command); }

String CommandProcessor::executeUnlocked(String command) {
  command.trim();
  command.toLowerCase();
  if (!command.length()) return "";
  if (command == "help" || command == "?") return
      "network dhcp\r\nnetwork static <IP> <MASK> <GATEWAY>\r\n"
      "network dns <DNS1> <DNS2>\r\nhostname <NAME>\r\n"
      "fan <1|2|all> <auto|0|1>\r\n"
      "temp curve [T1,T2]\r\ntemp read <1|2|all>\r\n"
      "config [pending|diff|discard|save]\r\n"
      "reboot | exit | logout | quit | help";
  if (command.startsWith("fan ")) return fanCommand(command);
  if (command.startsWith("temp ")) return temperatureCommand(command);
  if (command.startsWith("network ")) return editNetwork(command);
  if (command.startsWith("hostname ")) {
    const String hostname = wordAt(command, 1);
    if (!hostname.length() || hostname.length() >= sizeof(config_.edit().network.hostname))
      return "ERR: hostname length must be 1..31";
    hostname.toCharArray(config_.edit().network.hostname, sizeof(config_.edit().network.hostname));
    return "OK: candidate changed";
  }
  if (command == "config pending") return config_.pending() ? "Pending changes: yes" : "Pending changes: no";
  if (command == "config diff") return config_.diff();
  if (command == "config discard") { config_.discard(); return "OK: candidate discarded"; }
  if (command == "config save") return config_.save()
      ? "OK: startup and running config updated; reboot required for network changes"
      : "ERR: invalid configuration or EEPROM write failure";
  if (command == "reboot") { delay(100); NVIC_SystemReset(); }
  return "ERR: unknown command; use help";
}

String CommandProcessor::fanCommand(const String &command) {
  const String selected = wordAt(command, 1);
  const String action = wordAt(command, 2);
  if (selected != "1" && selected != "2" && selected != "all")
    return "ERR: usage: fan <1|2|all> <auto|0|1>";
  if (action != "auto" && action != "0" && action != "1")
    return "ERR: relay value must be 0 or 1";
  const uint8_t first = selected == "2" ? 2 : 1;
  const uint8_t last = selected == "1" ? 1 : 2;
  for (uint8_t fan = first; fan <= last; ++fan) {
    if (action == "auto") thermal_.setAutomatic(fan, true);
    else thermal_.setManualValue(fan, action == "1");
  }
  return "OK: " + selected + " set to " + action;
}

String CommandProcessor::temperatureCommand(const String &command) {
  const String action = wordAt(command, 1);
  if (action == "read") {
    const String selected = wordAt(command, 2);
    const TemperatureSnapshot &snapshot = temperatures_.snapshot();
    auto reading = [](const char *name, const TemperatureGroup &group) {
      return String(name) + ": " + (group.validCount ? String(group.mean, 2) + " C" : "FAULT");
    };
    if (selected == "1") return reading("TEMP1", snapshot.top);
    if (selected == "2") return reading("TEMP2", snapshot.bottom);
    if (selected == "all")
      return reading("TEMP1", snapshot.top) + "\r\n" + reading("TEMP2", snapshot.bottom);
    return "ERR: usage: temp read <1|2|all>";
  }
  if (action == "curve") {
    String values = command.substring(command.indexOf("curve") + 5);
    values.trim();
    if (values.startsWith("[") && values.endsWith("]"))
      values = values.substring(1, values.length() - 1);
    values.replace(',', ' ');
    values.trim();
    const String firstText = wordAt(values, 0);
    const String secondText = wordAt(values, 1);
    float first, second;
    if (!parseFloatStrict(firstText, first) || !parseFloatStrict(secondText, second) ||
        wordAt(values, 2).length() || first <= -20 || second >= 100 || first > second)
      return "ERR: usage: temp curve [T1,T2], with -20 < T1 <= T2 < 100";
    config_.edit().thermal.fan1OnC = first;
    config_.edit().thermal.fan2OnC = second;
    return "OK: candidate curve [" + String(first, 1) + "," + String(second, 1) + "]";
  }
  return "ERR: usage: temp <curve [T1,T2]|read 1|2|all>";
}

String CommandProcessor::editNetwork(const String &command) {
  const String action = wordAt(command, 1);
  if (action == "dhcp") {
    config_.edit().network.dhcp = true;
    return "OK: candidate changed";
  }
  if (action == "static") {
    IPAddress ip, mask, gateway;
    if (!ip.fromString(wordAt(command, 2)) || !mask.fromString(wordAt(command, 3)) ||
        !gateway.fromString(wordAt(command, 4)))
      return "ERR: usage: network static <IP> <MASK> <GATEWAY>";
    auto &network = config_.edit().network;
    network.dhcp = false;
    network.ip = static_cast<uint32_t>(ip);
    network.mask = static_cast<uint32_t>(mask);
    network.gateway = static_cast<uint32_t>(gateway);
    return "OK: candidate changed";
  }
  if (action == "dns") {
    IPAddress dns1, dns2;
    if (!dns1.fromString(wordAt(command, 2)) || !dns2.fromString(wordAt(command, 3)))
      return "ERR: usage: network dns <DNS1> <DNS2>";
    config_.edit().network.dns1 = static_cast<uint32_t>(dns1);
    config_.edit().network.dns2 = static_cast<uint32_t>(dns2);
    return "OK: candidate changed";
  }
  return "ERR: usage: network <dhcp|static|dns>";
}
