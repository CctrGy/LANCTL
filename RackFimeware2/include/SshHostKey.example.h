#pragma once

#include <cstddef>
#include <cstdint>

// Copia este archivo como SshHostKey.h y sustituye el marcador por una clave
// privada DER generada específicamente para tu dispositivo o instalación.
// SshHostKey.h está excluido de Git para impedir publicar la clave privada.
#error "Genera una clave SSH de host privada antes de compilar el firmware"

static const uint8_t SSH_HOST_KEY_DER[] = {0x00};
static constexpr size_t SSH_HOST_KEY_DER_SIZE = sizeof(SSH_HOST_KEY_DER);
