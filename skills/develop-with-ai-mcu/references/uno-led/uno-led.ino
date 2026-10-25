constexpr unsigned char LED_PIN = 8;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
  Serial.println("SIM_START UNO_R3 D8");
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  Serial.print("LED=");
  Serial.println(digitalRead(LED_PIN));
  delay(500);
  digitalWrite(LED_PIN, LOW);
  Serial.print("LED=");
  Serial.println(digitalRead(LED_PIN));
  delay(500);
}
