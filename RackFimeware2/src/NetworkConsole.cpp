#include "NetworkConsole.h"

#include <cstring>
#include <wolfssh/error.h>

#include "Config.h"
#include "SshHostKey.h"

int NetworkConsole::receiveCallback(WOLFSSH *, void *buffer, word32 size, void *context) {
  auto *client = static_cast<EthernetClient *>(context);
  if (!client || !client->connected()) return WS_CBIO_ERR_CONN_CLOSE;
  const int available = client->available();
  if (available <= 0) return WS_CBIO_ERR_WANT_READ;
  const int wanted = min<int>(available, static_cast<int>(size));
  const int received = client->read(static_cast<uint8_t *>(buffer), wanted);
  return received > 0 ? received : WS_CBIO_ERR_WANT_READ;
}

int NetworkConsole::sendCallback(WOLFSSH *, void *buffer, word32 size, void *context) {
  auto *client = static_cast<EthernetClient *>(context);
  if (!client || !client->connected()) return WS_CBIO_ERR_CONN_CLOSE;
  const size_t sent = client->write(static_cast<const uint8_t *>(buffer), size);
  return sent > 0 ? static_cast<int>(sent) : WS_CBIO_ERR_WANT_WRITE;
}

int NetworkConsole::authCallback(byte type, WS_UserAuthData *data, void *) {
  if (type != WOLFSSH_USERAUTH_PASSWORD || !data) return WOLFSSH_USERAUTH_FAILURE;
  const size_t userLength = strlen(SSH_USERNAME);
  const size_t passwordLength = strlen(SSH_PASSWORD);
  const bool userMatches = data->usernameSz == userLength &&
      memcmp(data->username, SSH_USERNAME, userLength) == 0;
  const bool passwordMatches = data->sf.password.passwordSz == passwordLength &&
      memcmp(data->sf.password.password, SSH_PASSWORD, passwordLength) == 0;
  return userMatches && passwordMatches ? WOLFSSH_USERAUTH_SUCCESS : WOLFSSH_USERAUTH_FAILURE;
}

bool NetworkConsole::begin() {
  line_.reserve(192);
  if (wolfSSH_Init() != WS_SUCCESS) return false;
  ctx_ = wolfSSH_CTX_new(WOLFSSH_ENDPOINT_SERVER, nullptr);
  if (!ctx_) return false;
  wolfSSH_SetIORecv(ctx_, receiveCallback);
  wolfSSH_SetIOSend(ctx_, sendCallback);
  wolfSSH_SetUserAuth(ctx_, authCallback);
  wolfSSH_CTX_SetBanner(ctx_, "RackMonitor Firmware 2 / STM32F411");
  // The wolfSSH desktop default reserves a 128 KiB receive window per
  // channel, which exhausts this MCU's RAM. The CLI only needs small packets.
  if (wolfSSH_CTX_SetWindowPacketSize(ctx_, 4096, 1024) != WS_SUCCESS) {
    return false;
  }
  if (wolfSSH_CTX_UsePrivateKey_buffer(ctx_, SSH_HOST_KEY_DER,
                                      SSH_HOST_KEY_DER_SIZE,
                                      WOLFSSH_FORMAT_ASN1) != WS_SUCCESS) {
    return false;
  }
  Serial.printf("SSH ready on TCP/%u (user: %s)\r\n", SSH_PORT, SSH_USERNAME);
  return true;
}

void NetworkConsole::acceptClient() {
  EthernetClient incoming = network_.consoleServer().available();
  if (!incoming) return;
  if (client_) { incoming.stop(); return; }
  client_ = incoming;
  ssh_ = wolfSSH_new(ctx_);
  if (!ssh_) { closeClient("wolfSSH_new failed"); return; }
  wolfSSH_SetIOReadCtx(ssh_, &client_);
  wolfSSH_SetIOWriteCtx(ssh_, &client_);
  state_ = State::HANDSHAKE;
  line_ = "";
  Serial.println("SSH client connected; negotiating session");
}

void NetworkConsole::closeClient(const char *reason) {
  if (reason) Serial.printf("SSH session closed: %s\r\n", reason);
  if (ssh_) {
    if (state_ == State::SHELL) wolfSSH_shutdown(ssh_);
    wolfSSH_free(ssh_);
    ssh_ = nullptr;
  }
  if (client_) client_.stop();
  state_ = State::LISTENING;
  line_ = "";
}

bool NetworkConsole::sendText(const String &text) {
  if (!ssh_ || !text.length()) return false;
  const int result = wolfSSH_stream_send(
      ssh_, reinterpret_cast<byte *>(const_cast<char *>(text.c_str())), text.length());
  return result == static_cast<int>(text.length());
}

void NetworkConsole::processLine() {
  line_.trim();
  String normalized = line_;
  normalized.toLowerCase();
  if (normalized == "exit" || normalized == "logout" || normalized == "quit") {
    sendText("Bye\r\n");
    closeClient();
    return;
  }
  const String response = commands_.execute(line_);
  if (response.length()) sendText(response + "\r\n");
  sendText("rackmonitor# ");
  line_ = "";
}

void NetworkConsole::update() {
  if (!ctx_) return;
  if (state_ == State::LISTENING) { acceptClient(); return; }
  if (!client_ || !client_.connected()) { closeClient("peer disconnected"); return; }

  if (state_ == State::HANDSHAKE) {
    const int result = wolfSSH_accept(ssh_);
    if (result == WS_SUCCESS) {
      state_ = State::SHELL;
      sendText("\r\nRackMonitor Firmware 2\r\nType 'help' for commands.\r\nrackmonitor# ");
      Serial.println("SSH authentication successful");
    } else {
      const int error = wolfSSH_get_error(ssh_);
      if (error != WS_WANT_READ && error != WS_WANT_WRITE) {
        closeClient(wolfSSH_ErrorToName(error));
      }
    }
    return;
  }

  byte buffer[64];
  const int received = wolfSSH_stream_read(ssh_, buffer, sizeof(buffer));
  if (received > 0) {
    for (int i = 0; i < received; ++i) {
      const char c = static_cast<char>(buffer[i]);
      if (c == 3 || c == 4) { closeClient(); return; }
      if (c == '\r' || c == '\n') {
        if (line_.length()) processLine();
      } else if ((c == 8 || c == 127) && line_.length()) {
        line_.remove(line_.length() - 1);
        sendText("\b \b");
      } else if (c >= 32 && c < 127 && line_.length() < 191) {
        line_ += c;
        sendText(String(c));
      }
    }
  } else {
    const int error = wolfSSH_get_error(ssh_);
    if (error != WS_WANT_READ && error != WS_WANT_WRITE) closeClient(wolfSSH_ErrorToName(error));
  }
}
