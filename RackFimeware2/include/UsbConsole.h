#pragma once

#include <Arduino.h>
#include "CommandProcessor.h"

class UsbConsole {
 public:
  explicit UsbConsole(CommandProcessor &commands) : commands_(commands) {}
  void begin();
  void update();
 private:
  CommandProcessor &commands_;
  String line_;
  bool sessionActive_ = true;
  void printBanner();
  void executeLine();
};
