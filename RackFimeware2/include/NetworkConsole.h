#pragma once

#include <EthernetENC.h>
#include <wolfssh/ssh.h>

#include "CommandProcessor.h"
#include "NetworkService.h"

class NetworkConsole {
 public:
  NetworkConsole(CommandProcessor &commands, NetworkService &network)
      : commands_(commands), network_(network) {}
  bool begin();
  void update();

 private:
  enum class State : uint8_t { LISTENING, HANDSHAKE, SHELL };
  CommandProcessor &commands_;
  NetworkService &network_;
  EthernetClient client_;
  WOLFSSH_CTX *ctx_ = nullptr;
  WOLFSSH *ssh_ = nullptr;
  State state_ = State::LISTENING;
  String line_;

  void acceptClient();
  void closeClient(const char *reason = nullptr);
  void processLine();
  bool sendText(const String &text);
  static int receiveCallback(WOLFSSH *, void *, word32, void *);
  static int sendCallback(WOLFSSH *, void *, word32, void *);
  static int authCallback(byte, WS_UserAuthData *, void *);
};
