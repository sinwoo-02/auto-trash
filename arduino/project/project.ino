#include <Servo.h>

Servo servo;
Servo gServo1, gServo2;   // 일반 쓰레기 서보
Servo pServo1, pServo2;   // 플라스틱 쓰레기 서보

const int SERVO = 11; //슬라이딩 도어
const int G_SERVO_PIN_1 = 5; // 뒤면쪽
const int G_SERVO_PIN_2 = 3; // 앞면쪽
const int P_SERVO_PIN_1 = 9; // 뒤면쪽
const int P_SERVO_PIN_2 = 6; // 앞면쪽
const int RED_PIN = 12; // 빨간색 LED
const int TRIG_PIN = 4; // 트리거 핀
const int ECHO_PIN = 2; // 에코 핀

const int GENERAL_OPEN_ANGLE_1 = 80;
const int GENERAL_OPEN_ANGLE_2 = 100;
const int GENERAL_CLOSE_ANGLE_1 = 0;
const int GENERAL_CLOSE_ANGLE_2 = 180;

const int PLASTIC_OPEN_ANGLE_1 = 80;
const int PLASTIC_OPEN_ANGLE_2 = 100;
const int PLASTIC_CLOSE_ANGLE_1 = 0;
const int PLASTIC_CLOSE_ANGLE_2 = 180;

const int BIN_FULL_THRESHOLD_CM = 17; // 초음파 임계 거리

String trashType = "";
String contamination = "";

int measureDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms 타임아웃

  if (duration == 0)
    return 999;  // 측정 실패

  return duration * 0.034 / 2;
}

void trashIn(){
  servo.attach(SERVO);
  delay(7000);
  servo.detach();
}

void checkBinLevel(int ledPin, int thresholdCm) {
  int distance = measureDistance();
  digitalWrite(ledPin, (distance <= thresholdCm) ? HIGH : LOW);
  Serial.print(distance);
  Serial.println("cm");
}

void setGateAngles(Servo& s1, Servo& s2, int angle1, int angle2) {
  s1.write(angle1);
  s2.write(angle2);
}

void processGeneralTrash() {
  setGateAngles(gServo1, gServo2, GENERAL_OPEN_ANGLE_1, GENERAL_OPEN_ANGLE_2);
  trashIn();
  delay(3000);
  setGateAngles(gServo1, gServo2, GENERAL_CLOSE_ANGLE_1, GENERAL_CLOSE_ANGLE_2);

  checkBinLevel(RED_PIN, BIN_FULL_THRESHOLD_CM);
}

void processPlasticTrash(bool contaminated) {

  // 오염된 플라스틱 (일반/다른 구역에 처리할 경우)
  if (contaminated) {
    Serial.println("contaminated plastic detected");
    return;
  }

  // 깨끗한 플라스틱
  setGateAngles(pServo1, pServo2, PLASTIC_OPEN_ANGLE_1, PLASTIC_OPEN_ANGLE_2);
  trashIn();
  delay(3000);
  setGateAngles(pServo1, pServo2, PLASTIC_CLOSE_ANGLE_1, PLASTIC_CLOSE_ANGLE_2);
}

void processCans() {
  trashIn();
}

void setup() {
  Serial.begin(9600);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(RED_PIN, OUTPUT);

  gServo1.attach(G_SERVO_PIN_1);
  gServo2.attach(G_SERVO_PIN_2);
  pServo1.attach(P_SERVO_PIN_1);
  pServo2.attach(P_SERVO_PIN_2);

  gServo1.write(0);
  gServo2.write(0);
  pServo1.write(0);
  pServo2.write(0);
}

void loop() {

  String data = ""; 

  if (Serial.available()) {
    data = Serial.readStringUntil('\n');
    data.trim();

    int idx = data.indexOf(',');
    if (idx != -1) {
      trashType = data.substring(0, idx);
      contamination = data.substring(idx + 1);
    }

    trashType.toUpperCase();
    contamination.toUpperCase();

    if (trashType == "G") {
      Serial.println(trashType);
      processGeneralTrash();
    }
    else if (trashType == "P") {
      Serial.println(trashType + " : " + contamination);
      bool isContaminated = (contamination == "N");
      processPlasticTrash(isContaminated);
    }
    else if (trashType == "C") {
      Serial.println(trashType);
      processCans();
    }
    else {
      Serial.println("unknown");
    }
    while (Serial.available()) {
        Serial.read();
    }
  }

  delay(20);
}