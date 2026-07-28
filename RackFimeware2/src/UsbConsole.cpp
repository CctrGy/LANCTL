#include "UsbConsole.h"

void UsbConsole::printBanner() {
  Serial.println(); Serial.println("RackMonitor Firmware 2 / STM32F411 - USB CLI");
  Serial.println("Type 'help' for commands."); Serial.print("rackmonitor# ");
}
void UsbConsole::begin() { line_.reserve(256); printBanner(); }
void UsbConsole::executeLine() {
  line_.trim();
  if (!line_.length()) { Serial.print("rackmonitor# "); return; }
  String normalized = line_; normalized.toLowerCase();
  if (normalized == "exit" || normalized == "logout" || normalized == "quit") {
    Serial.println("USB CLI session closed. Press Enter to reopen."); sessionActive_ = false; line_ = ""; return;
  }
  const String response = commands_.execute(line_); if (response.length()) Serial.println(response);
  line_ = ""; Serial.print("rackmonitor# ");
}
void UsbConsole::update() {
  while (Serial.available()) {
    const char c = static_cast<char>(Serial.read());
    if (!sessionActive_) { if (c == '\r' || c == '\n') { sessionActive_ = true; printBanner(); } continue; }
    if (c == '\r' || c == '\n') { Serial.println(); executeLine(); }
    else if ((c == 8 || c == 127) && line_.length()) { line_.remove(line_.length()-1); Serial.print("\b \b"); }
    else if (c >= 32 && c < 127 && line_.length() < 255) { line_ += c; Serial.print(c); }
  }
}
