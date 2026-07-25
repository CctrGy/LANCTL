#include <Arduino.h>
#include <SPI.h>

namespace Pins {
constexpr uint8_t RESET = 10;
constexpr uint8_t CS = 16;
constexpr uint8_t SCK = 15;
constexpr uint8_t MOSI = 7;  // ENC28J60 SI
constexpr uint8_t MISO = 6;  // ENC28J60 SO
constexpr uint8_t INT = 17;
constexpr uint8_t FAN1_RELAY = 11;
constexpr uint8_t FAN2_RELAY = 12;
}

namespace Enc {
constexpr uint8_t RCR = 0x00;
constexpr uint8_t WCR = 0x40;
constexpr uint8_t BFS = 0x80;
constexpr uint8_t BFC = 0xA0;
constexpr uint8_t SRC = 0xFF;
constexpr uint8_t EIE = 0x1B;
constexpr uint8_t EIR = 0x1C;
constexpr uint8_t ESTAT = 0x1D;
constexpr uint8_t ECON2 = 0x1E;
constexpr uint8_t ECON1 = 0x1F;
constexpr uint8_t EREVID = 0x12;
constexpr uint8_t BANK_MASK = 0x03;
}

SPIClass diagnosticSpi(FSPI);

void selectChip() { digitalWrite(Pins::CS, LOW); }
void releaseChip() { digitalWrite(Pins::CS, HIGH); }

uint8_t readRegister(uint8_t address, bool dummyByte = false) {
  selectChip();
  diagnosticSpi.transfer(Enc::RCR | (address & 0x1F));
  if (dummyByte) diagnosticSpi.transfer(0x00);
  const uint8_t value = diagnosticSpi.transfer(0x00);
  releaseChip();
  return value;
}

void bitFieldClear(uint8_t address, uint8_t mask) {
  selectChip();
  diagnosticSpi.transfer(Enc::BFC | (address & 0x1F));
  diagnosticSpi.transfer(mask);
  releaseChip();
}

void bitFieldSet(uint8_t address, uint8_t mask) {
  selectChip();
  diagnosticSpi.transfer(Enc::BFS | (address & 0x1F));
  diagnosticSpi.transfer(mask);
  releaseChip();
}

void selectBank(uint8_t bank) {
  bitFieldClear(Enc::ECON1, Enc::BANK_MASK);
  bitFieldSet(Enc::ECON1, bank & Enc::BANK_MASK);
}

void softReset() {
  selectChip();
  diagnosticSpi.transfer(Enc::SRC);
  releaseChip();
  delay(2);
}

void hardwareReset() {
  digitalWrite(Pins::RESET, LOW);
  delay(20);
  digitalWrite(Pins::RESET, HIGH);
  delay(100);
}

void printBinary(uint8_t value) {
  for (int8_t bit = 7; bit >= 0; --bit) Serial.print((value >> bit) & 1);
}

void printRegister(const char *name, uint8_t address, bool dummy = false) {
  const uint8_t value = readRegister(address, dummy);
  Serial.printf("  %-6s addr=0x%02X value=0x%02X binary=", name, address, value);
  printBinary(value);
  Serial.println();
}

void runProbe(uint32_t frequency, uint8_t mode) {
  diagnosticSpi.beginTransaction(SPISettings(frequency, MSBFIRST, mode));
  hardwareReset();
  softReset();

  Serial.printf("\n--- SPI probe: frequency=%lu Hz mode=%u ---\n",
                static_cast<unsigned long>(frequency), mode);
  Serial.printf("  Pin levels before reads: MISO=%d INT=%d RESET=%d CS=%d\n",
                digitalRead(Pins::MISO), digitalRead(Pins::INT),
                digitalRead(Pins::RESET), digitalRead(Pins::CS));
  printRegister("EIE", Enc::EIE);
  printRegister("EIR", Enc::EIR);
  printRegister("ESTAT", Enc::ESTAT);
  printRegister("ECON2", Enc::ECON2);
  printRegister("ECON1", Enc::ECON1);
  selectBank(3);
  printRegister("EREVID", Enc::EREVID);
  selectBank(0);
  diagnosticSpi.endTransaction();
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  pinMode(Pins::CS, OUTPUT);
  pinMode(Pins::RESET, OUTPUT);
  pinMode(Pins::INT, INPUT_PULLUP);
  pinMode(Pins::MISO, INPUT);
  pinMode(Pins::FAN1_RELAY, OUTPUT);
  pinMode(Pins::FAN2_RELAY, OUTPUT);
  digitalWrite(Pins::FAN1_RELAY, HIGH);
  digitalWrite(Pins::FAN2_RELAY, HIGH);
  releaseChip();
  digitalWrite(Pins::RESET, HIGH);
  diagnosticSpi.begin(Pins::SCK, Pins::MISO, Pins::MOSI, Pins::CS);

  Serial.println();
  Serial.println("=================================================");
  Serial.println("ENC28J60 RAW SPI DIAGNOSTIC");
  Serial.println("=================================================");
  Serial.printf("Pins: RESET=%u CS=%u SCK=%u SI/MOSI=%u SO/MISO=%u INT=%u\n",
                Pins::RESET, Pins::CS, Pins::SCK, Pins::MOSI, Pins::MISO, Pins::INT);
  Serial.println("Safety: FAN1 and FAN2 relays forced ON during diagnostics.");
  Serial.println("Expected EREVID for a real ENC28J60 is commonly 0x05 or 0x06.");
  Serial.println("All 0x00 often means MISO stuck LOW; all 0xFF often means floating/HIGH.");

  const uint32_t frequencies[] = {500000, 1000000, 2000000, 4000000, 8000000, 10000000};
  for (uint8_t mode = 0; mode < 4; ++mode) {
    for (uint32_t frequency : frequencies) runProbe(frequency, mode);
  }
  Serial.println("\nDiagnostic sweep complete. It will repeat every 10 seconds.");
}

void loop() {
  delay(10000);
  runProbe(8000000, SPI_MODE0);
}
