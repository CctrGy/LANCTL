#include <Arduino.h>
#include <LittleFS.h>
#include <WiFi.h>

#include "CommandProcessor.h"
#include "Config.h"
#include "libssh_esp32.h"
#include <libssh/libssh.h>
#include <libssh/server.h>

namespace {
constexpr char HOST_KEY[] = "/littlefs/ssh_host_ed25519_key";
constexpr uint32_t SSH_STACK_SIZE = 16384;

bool ensureHostKey() {
  if (LittleFS.exists("/ssh_host_ed25519_key")) return true;
  Serial.println("Generating SSH host key (first boot)...");
  ssh_key key = nullptr;
  if (ssh_pki_generate(SSH_KEYTYPE_ED25519, 0, &key) != SSH_OK) return false;
  const int result = ssh_pki_export_privkey_file(key, nullptr, nullptr, nullptr, HOST_KEY);
  ssh_key_free(key);
  return result == SSH_OK;
}

bool authenticate(ssh_session session) {
  while (ssh_is_connected(session)) {
    ssh_message message = ssh_message_get(session);
    if (!message) return false;
    bool accepted = false;
    if (ssh_message_type(message) == SSH_REQUEST_AUTH &&
        ssh_message_subtype(message) == SSH_AUTH_METHOD_PASSWORD) {
      const char *user = ssh_message_auth_user(message);
      const char *password = ssh_message_auth_password(message);
      accepted = user && password && strcmp(user, SSH_USERNAME) == 0 && strcmp(password, SSH_PASSWORD) == 0;
    }
    if (accepted) {
      ssh_message_auth_reply_success(message, 0);
      ssh_message_free(message);
      return true;
    }
    ssh_message_auth_set_methods(message, SSH_AUTH_METHOD_PASSWORD);
    ssh_message_reply_default(message);
    ssh_message_free(message);
  }
  return false;
}

ssh_channel openShell(ssh_session session) {
  ssh_channel channel = nullptr;
  while (ssh_is_connected(session) && !channel) {
    ssh_message message = ssh_message_get(session);
    if (!message) return nullptr;
    if (ssh_message_type(message) == SSH_REQUEST_CHANNEL_OPEN &&
        ssh_message_subtype(message) == SSH_CHANNEL_SESSION) {
      channel = ssh_message_channel_request_open_reply_accept(message);
    } else {
      ssh_message_reply_default(message);
    }
    ssh_message_free(message);
  }
  if (!channel) return nullptr;

  bool shellRequested = false;
  while (ssh_is_connected(session) && !shellRequested) {
    ssh_message message = ssh_message_get(session);
    if (!message) break;
    if (ssh_message_type(message) == SSH_REQUEST_CHANNEL) {
      const int subtype = ssh_message_subtype(message);
      if (subtype == SSH_CHANNEL_REQUEST_PTY) {
        ssh_message_channel_request_reply_success(message);
      } else if (subtype == SSH_CHANNEL_REQUEST_SHELL) {
        ssh_message_channel_request_reply_success(message);
        shellRequested = true;
      } else {
        ssh_message_reply_default(message);
      }
    } else {
      ssh_message_reply_default(message);
    }
    ssh_message_free(message);
  }
  if (!shellRequested) {
    ssh_channel_close(channel);
    ssh_channel_free(channel);
    return nullptr;
  }
  return channel;
}

void writeText(ssh_channel channel, const String &text) {
  if (text.length()) ssh_channel_write(channel, text.c_str(), text.length());
}

void runConsole(ssh_channel channel, CommandProcessor &commands) {
  writeText(channel, "RackMonitor Hardware V1\r\nType 'help' for commands.\r\nrackmonitor> ");
  String line;
  while (ssh_channel_is_open(channel) && !ssh_channel_is_eof(channel)) {
    char buffer[64];
    const int received = ssh_channel_read_timeout(channel, buffer, sizeof(buffer), 0, 250);
    if (received == SSH_ERROR) break;
    for (int i = 0; i < received; ++i) {
      const char c = buffer[i];
      if (c == 3 || c == 4) return;
      if (c == '\r' || c == '\n') {
        if (!line.length()) continue;
        writeText(channel, "\r\n");
        String normalized = line;
        normalized.trim();
        normalized.toLowerCase();
        if (normalized == "exit" || normalized == "logout" || normalized == "quit") {
          writeText(channel, "Bye\r\n");
          return;
        }
        const String response = commands.execute(line);
        writeText(channel, response);
        writeText(channel, "\r\nrackmonitor> ");
        line = "";
      } else if ((c == 8 || c == 127) && line.length()) {
        line.remove(line.length() - 1);
        writeText(channel, "\b \b");
      } else if (c >= 32 && c < 127 && line.length() < 255) {
        line += c;
        ssh_channel_write(channel, &c, 1);
      }
    }
    vTaskDelay(1);
  }
}

void sshTask(void *parameter) {
  auto &commands = *static_cast<CommandProcessor *>(parameter);
  libssh_begin();
  if (!ensureHostKey()) {
    Serial.println("ERROR: could not create SSH host key");
    vTaskDelete(nullptr);
  }

  ssh_bind binding = ssh_bind_new();
  if (!binding) vTaskDelete(nullptr);
  int port = SSH_PORT;
  ssh_bind_options_set(binding, SSH_BIND_OPTIONS_BINDPORT, &port);
  ssh_bind_options_set(binding, SSH_BIND_OPTIONS_HOSTKEY, HOST_KEY);
  // WiFiServer owns the listening socket. This is more reliable with the
  // Arduino ESP32/LwIP integration than libssh's POSIX bind/listen wrapper.
  WiFiServer server(port);
  server.begin();
  server.setNoDelay(true);
  Serial.printf("SSH ready on port %d (user: %s)\n", port, SSH_USERNAME);

  for (;;) {
    WiFiClient client = server.available();
    if (!client) {
      vTaskDelay(pdMS_TO_TICKS(20));
      continue;
    }
    const int sessionFd = client.fd();
    ssh_session session = ssh_new();
    if (!session) {
      client.stop();
      vTaskDelay(pdMS_TO_TICKS(1000));
      continue;
    }
    const int accepted = ssh_bind_accept_fd(binding, session, sessionFd);
    if (accepted == SSH_OK && ssh_handle_key_exchange(session) == SSH_OK && authenticate(session)) {
      ssh_channel channel = openShell(session);
      if (channel) {
        runConsole(channel, commands);
        ssh_channel_send_eof(channel);
        ssh_channel_close(channel);
        ssh_channel_free(channel);
      }
    } else {
      Serial.printf("SSH connection ended: %s\n", ssh_get_error(session));
    }
    ssh_disconnect(session);
    ssh_free(session);
  }
}
}

void startSshServer(CommandProcessor &commands) {
  xTaskCreatePinnedToCore(sshTask, "ssh-server", SSH_STACK_SIZE, &commands,
                          tskIDLE_PRIORITY + 2, nullptr, 0);
}
