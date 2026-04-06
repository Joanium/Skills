---
name: EmbeddedSystemsIoT
description: Design and develop embedded systems and IoT solutions including firmware, RTOS, microcontroller programming, sensor integration, communication protocols (MQTT, CoAP, BLE, Zigbee), and cloud connectivity. Use when the user asks about Arduino, ESP32, Raspberry Pi, STM32, FreeRTOS, hardware interfaces, or IoT data pipelines.
---

You are an expert in embedded systems and IoT development, covering firmware development in C/C++/MicroPython, real-time operating systems, hardware communication protocols, sensor integration, low-power design, and IoT cloud connectivity.

The user provides an embedded/IoT task: writing firmware, configuring peripherals, designing RTOS tasks, implementing communication protocols, integrating sensors, optimizing power consumption, or connecting devices to cloud platforms.

## Platform Selection

| Platform          | MCU                                | Use Case                                 |
| ----------------- | ---------------------------------- | ---------------------------------------- |
| Arduino Uno/Nano  | ATmega328P (8-bit, 16MHz, 2KB RAM) | Simple prototyping, educational          |
| Arduino Mega      | ATmega2560                         | More pins/memory for complex prototypes  |
| ESP32             | Xtensa LX6 240MHz, 520KB RAM       | WiFi + BLE, IoT endpoints, ML inference  |
| ESP8266           | 80MHz, 80KB RAM                    | Cheap WiFi-only IoT nodes                |
| Raspberry Pi Pico | RP2040 dual-core 133MHz            | Python/C, PIO for custom protocols       |
| STM32             | ARM Cortex-M (various)             | Industrial, high-performance, RTOS-ready |
| nRF52840          | ARM Cortex-M4, BLE 5.0             | BLE-primary devices, Thread, Zigbee      |
| Raspberry Pi 4/5  | ARM Cortex-A (Linux)               | Edge compute, camera, full OS needed     |

## Firmware Fundamentals (C/C++)

**GPIO Bare-Metal (STM32 HAL)**

```c
// Initialize LED pin
GPIO_InitTypeDef GPIO_InitStruct = {0};
__HAL_RCC_GPIOC_CLK_ENABLE();
GPIO_InitStruct.Pin = GPIO_PIN_13;
GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
GPIO_InitStruct.Pull = GPIO_NOPULL;
GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

// Toggle LED
HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
HAL_Delay(500);
```

**Arduino C++ (ESP32)**

```cpp
#include <Arduino.h>

const int LED_PIN = 2;
const int BUTTON_PIN = 0;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
}

void loop() {
  if (digitalRead(BUTTON_PIN) == LOW) {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("Button pressed");
  } else {
    digitalWrite(LED_PIN, LOW);
  }
}
```

**MicroPython (Raspberry Pi Pico)**

```python
from machine import Pin, ADC
import time

led = Pin(25, Pin.OUT)
adc = ADC(Pin(26))  # ADC0

while True:
    reading = adc.read_u16()  # 0–65535
    voltage = reading * 3.3 / 65535
    print(f"Voltage: {voltage:.2f}V")
    led.toggle()
    time.sleep(0.5)
```

## Hardware Communication Protocols

**I2C**

```cpp
// ESP32 Arduino — scan for I2C devices
#include <Wire.h>

Wire.begin(SDA_PIN, SCL_PIN);  // Default: SDA=21, SCL=22 on ESP32

for (byte addr = 1; addr < 127; addr++) {
  Wire.beginTransmission(addr);
  if (Wire.endTransmission() == 0) {
    Serial.printf("Device found at 0x%02X\n", addr);
  }
}

// Read from BME280 temperature sensor
Wire.beginTransmission(0x76);
Wire.write(0xF7);  // Register address for pressure/temp/humidity
Wire.endTransmission(false);
Wire.requestFrom(0x76, 8);
```

**SPI**

```cpp
#include <SPI.h>

SPI.begin(SCK, MISO, MOSI, CS);
SPI.beginTransaction(SPISettings(8000000, MSBFIRST, SPI_MODE0));

digitalWrite(CS, LOW);
byte response = SPI.transfer(0x9F);  // Send command, receive response
digitalWrite(CS, HIGH);

SPI.endTransaction();
```

**UART**

```cpp
// Software serial for sensors on ESP32
Serial2.begin(9600, SERIAL_8N1, RX_PIN, TX_PIN);

if (Serial2.available()) {
  String line = Serial2.readStringUntil('\n');
  Serial.println("GPS: " + line);
}
```

**PWM**

```cpp
// ESP32 LEDC (PWM controller)
const int PWM_CHANNEL = 0;
const int PWM_FREQ = 5000;   // Hz
const int PWM_RESOLUTION = 8; // bits (0–255)

ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
ledcAttachPin(SERVO_PIN, PWM_CHANNEL);

// Control servo: 0° = 1ms pulse, 90° = 1.5ms, 180° = 2ms
// At 50Hz: duty 0–255 maps to 0–20ms period
int duty = map(angle, 0, 180, 13, 26);  // Approx for 50Hz, 8-bit
ledcWrite(PWM_CHANNEL, duty);
```

## FreeRTOS on ESP32

**Task Creation**

```cpp
void sensorTask(void *pvParameters) {
  TickType_t xLastWakeTime = xTaskGetTickCount();

  while (true) {
    float temp = readTemperature();
    float humidity = readHumidity();

    // Send to queue (non-blocking)
    SensorData data = { temp, humidity, millis() };
    xQueueSend(sensorQueue, &data, 0);

    // Run every 1000ms
    vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(1000));
  }
}

void networkTask(void *pvParameters) {
  SensorData data;
  while (true) {
    if (xQueueReceive(sensorQueue, &data, portMAX_DELAY)) {
      publishToMQTT(data);
    }
  }
}

void setup() {
  sensorQueue = xQueueCreate(10, sizeof(SensorData));

  xTaskCreatePinnedToCore(sensorTask, "Sensor", 4096, NULL, 2, NULL, 0);  // Core 0
  xTaskCreatePinnedToCore(networkTask, "Network", 8192, NULL, 1, NULL, 1); // Core 1
}
```

**Semaphores & Mutexes**

```cpp
SemaphoreHandle_t i2cMutex = xSemaphoreCreateMutex();

void readSensor() {
  if (xSemaphoreTake(i2cMutex, pdMS_TO_TICKS(100))) {
    // Safe to use I2C
    float val = sensor.read();
    xSemaphoreGive(i2cMutex);
    return val;
  }
}
```

## MQTT (IoT Messaging)

```cpp
#include <WiFi.h>
#include <PubSubClient.h>

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

void callback(char* topic, byte* payload, unsigned int length) {
  String msg = String((char*)payload).substring(0, length);
  Serial.printf("Received [%s]: %s\n", topic, msg.c_str());

  if (String(topic) == "device/joanium/cmd") {
    DynamicJsonDocument doc(256);
    deserializeJson(doc, msg);
    if (doc["action"] == "toggle_led") {
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    }
  }
}

void connectMQTT() {
  mqtt.setServer("broker.hivemq.com", 1883);
  mqtt.setCallback(callback);

  while (!mqtt.connected()) {
    String clientId = "ESP32-" + String(random(0xffff), HEX);
    if (mqtt.connect(clientId.c_str(), "user", "pass")) {
      mqtt.subscribe("device/joanium/cmd");
      mqtt.publish("device/joanium/status", "{\"online\":true}");
    } else {
      delay(5000);
    }
  }
}

void loop() {
  if (!mqtt.connected()) connectMQTT();
  mqtt.loop();

  // Publish sensor data every 10s
  static unsigned long lastPublish = 0;
  if (millis() - lastPublish > 10000) {
    char payload[128];
    snprintf(payload, sizeof(payload),
      "{\"temp\":%.2f,\"humidity\":%.2f,\"uptime\":%lu}",
      readTemp(), readHumidity(), millis() / 1000);
    mqtt.publish("device/joanium/telemetry", payload);
    lastPublish = millis();
  }
}
```

## BLE (Bluetooth Low Energy)

```cpp
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

#define SERVICE_UUID        "12345678-1234-5678-1234-56789abcdef0"
#define CHARACTERISTIC_UUID "abcdef01-1234-5678-1234-56789abcdef0"

BLECharacteristic *pCharacteristic;

class ServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) { Serial.println("Client connected"); }
  void onDisconnect(BLEServer* pServer) {
    BLEDevice::startAdvertising();  // Restart advertising after disconnect
  }
};

class CharCallbacks: public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    std::string value = pCharacteristic->getValue();
    Serial.printf("Received: %s\n", value.c_str());
  }
};

void setup() {
  BLEDevice::init("Joanium-Sensor");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new ServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);
  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_NOTIFY
  );
  pCharacteristic->setCallbacks(new CharCallbacks());
  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  BLEDevice::startAdvertising();
}
```

## Low-Power Design

**ESP32 Sleep Modes**

```cpp
// Light sleep — RAM retained, GPIO can wake
esp_sleep_enable_gpio_wakeup();
gpio_wakeup_enable(GPIO_NUM_0, GPIO_INTR_LOW_LEVEL);
esp_light_sleep_start();

// Deep sleep — only RTC RAM retained; lowest power (~10µA)
esp_sleep_enable_timer_wakeup(30 * 1000000ULL);  // Wake after 30 seconds
Serial.flush();
esp_deep_sleep_start();

// On wake from deep sleep, check reason
esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
if (cause == ESP_SLEEP_WAKEUP_TIMER) {
  // Timer wakeup — do sensor read and publish
}
```

**Power Budget Planning**

- Measure current with a Nordic PPK2 or INA219 current sensor
- Calculate mAh: `current_mA × duty_cycle_time_h = mAh consumed`
- Typical ESP32 active: ~80–240mA; deep sleep: ~10µA
- 2000mAh battery ÷ 1mAh avg = 2000 hours (83 days) runtime

## OTA Updates (ESP32)

```cpp
#include <ArduinoOTA.h>

void setupOTA() {
  ArduinoOTA.setHostname("joanium-sensor");
  ArduinoOTA.setPassword("secure-ota-password");

  ArduinoOTA.onStart([]() { Serial.println("OTA Start"); });
  ArduinoOTA.onEnd([]() { Serial.println("OTA End"); });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("OTA Error[%u]\n", error);
  });
  ArduinoOTA.begin();
}

void loop() {
  ArduinoOTA.handle();  // Must call every loop
  // ... rest of loop
}
```

## Cloud Connectivity

- **AWS IoT Core**: X.509 certificates + MQTT; use `esp-aws-iot` library
- **Google Cloud IoT Core**: JWT auth + MQTT/HTTP; `arduino-mqtt` compatible
- **Azure IoT Hub**: SAS token auth; supports MQTT and AMQP
- **Home Assistant**: MQTT auto-discovery; expose devices with config JSON on `homeassistant/sensor/device_id/config` topic
- **Blynk**: Simple mobile dashboard; Blynk.virtualWrite(V0, value) API
- **InfluxDB + Grafana**: Time-series storage with beautiful dashboards; use `influxdb-client-arduino`
