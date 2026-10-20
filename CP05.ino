
#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

// WIFI
const char* WIFI_SSID = "FIAP_IOT2";
const char* WIFI_PASSWORD = "F!@p25.IOT";

// MQTT
const char* MQTT_SERVER = "3.135.234.101";
const int MQTT_PORT = 1883;
const char* TOPIC_RFID = "smartgym/ali/cp05/rfid";

// RFID
#define SS_PIN 5
#define RST_PIN 22

MFRC522 rfid(SS_PIN, RST_PIN);

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

void conectarWiFi() {
  Serial.print("Conectando ao Wi-Fi");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void conectarMQTT() {
  while (!mqtt.connected()) {
    Serial.print("Conectando ao MQTT... ");

    String clientId = "SmartGym-ESP32-";
    clientId += String((uint32_t)ESP.getEfuseMac(), HEX);

    if (mqtt.connect(clientId.c_str())) {
      Serial.println("conectado!");
    } else {
      Serial.print("Falhou, rc=");
      Serial.println(mqtt.state());
      delay(3000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  SPI.begin(18, 19, 23, SS_PIN);
  rfid.PCD_Init();

  conectarWiFi();

  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  conectarMQTT();

  Serial.println("SMART GYM PRONTO!");
  Serial.println("Aproxime um cartao RFID.");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    conectarWiFi();
  }

  if (!mqtt.connected()) {
    conectarMQTT();
  }

  mqtt.loop();

  if (!rfid.PICC_IsNewCardPresent()) {
    return;
  }

  if (!rfid.PICC_ReadCardSerial()) {
    return;
  }

  String uid = "";

  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) {
      uid += "0";
    }

    uid += String(rfid.uid.uidByte[i], HEX);
  }

  uid.toUpperCase();

  String payload = "{\"uid\":\"" + uid +
                   "\",\"origem\":\"ESP32_WIFI\"}";

  Serial.print("Cartao identificado: ");
  Serial.println(uid);

  if (mqtt.publish(TOPIC_RFID, payload.c_str())) {
    Serial.println("UID enviado ao MQTT!");
  } else {
    Serial.println("Falha ao publicar UID.");
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(1500);
}
