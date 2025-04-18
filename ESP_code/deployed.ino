/*
Hardware Implementation Steps
Component Assembly
Connect ESP32 GPIO pins to sensors:
• DS18B20 Temperature: GPIO 4 (1-Wire)
• TDS Sensor: GPIO 32 (Analog)
• pH Sensor: GPIO 36 (Analog)
• OLED Display: IC (SDA=GPIO 21, SCL=GPIO 22)
• Use 3.3V power for all sensors except pH (5V)
• Add 4.7KQ resistor between VCC and DATA for DS18B20
*/
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "Hello";
const char* password = "bhairu02";

const char* serverName = "https://real-time-water-monitoring-system.onrender.com/esp32";

#define PH_SENSOR_OFFSET -1.24
#define PH_SENSOR_SCALE 6.84 
#define CALIBRATION_FACTOR 0.65
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#define ONE_WIRE_BUS 4  // GPIO pin for DS18B20 sensor
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempsensor(&oneWire);

#define TDS_PIN 32
const int potPin = A0;
float ph = 0;
float TDSValue = 0;
float t = 0;

void setup(void) {
    Serial.begin(9600);
    WiFi.begin(ssid, password);

    // Connect to WiFi
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi");

    tempsensor.begin();
    pinMode(potPin, INPUT);

    display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS);
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println("TDS, -pH, -Temp");
    display.display();
    delay(2000);

}

void loop(void) {
   // client.poll();

    readTemperature();
    readTDS();
    readPh();
    delay(2); // allow CPU to switch to other tasks

    display.clearDisplay();
    display.setCursor(0, 0);
    display.print("TDS:-");
    display.println(TDSValue);
    display.print("pH:-");
    display.println(ph);
    display.print("Temp:-");
    display.print(t);
    display.println("-C");
    display.display();

    if(WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    // Create JSON payload
    String httpRequestData = "{\"temperature\":";
    httpRequestData += String(t, 2);
    httpRequestData += ",\"tds\":";
    httpRequestData += String(TDSValue, 2);
    httpRequestData += ",\"ph\":";
    httpRequestData += String(ph, 2);
    httpRequestData += "}";

    int httpResponseCode = http.POST(httpRequestData);

    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);

    String response = http.getString();
    Serial.println(response);

    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }

  delay(3000); // Send every 3 seconds
}

float readTemperature() {
    tempsensor.requestTemperatures();
    t = tempsensor.getTempCByIndex(0);
    if (isnan(t)) {
        return -1;
    } else {
        Serial.print(t);
        Serial.print(",");
        return t;
    }
}

float readPh() {
    float pHValue = analogRead(potPin);
    float voltage = pHValue * (3.3 / 4095.0);
    ph = PH_SENSOR_SCALE * voltage + PH_SENSOR_OFFSET;
    Serial.println(ph); 
    return ph;
}

float readTDS() {
    float rawValue = analogRead(TDS_PIN);
    float voltage = rawValue * (3.3 / 4095.0);
    TDSValue = (133.42 * voltage * voltage * voltage - 255.86 * voltage * voltage + 857.39 * voltage) * CALIBRATION_FACTOR;
    TDSValue = TDSValue / (1.0 + 0.02 * (t - 25.0));
    Serial.print(TDSValue);
    Serial.print(",");
    return TDSValue;
}