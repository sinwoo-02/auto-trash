# ♻️ Smart Trash Sorting System (스마트 쓰레기 자동 분류 시스템)

> **AI 비전 인식(2-Stage 딥러닝)과 임베디드 메카트로닉스를 융합한 지능형 재활용 쓰레기 자동 분류 시스템**  
> 캡스톤 디자인 프로젝트 (AI Convergence Capstone Design)

---

## 📌 목차
1. [프로젝트 개요](#-프로젝트-개요)
2. [핵심 기능](#-핵심-기능)
3. [시스템 아키텍처 및 파이프라인](#-시스템-아키텍처-및-파이프라인)
4. [기술 스택 (Tech Stack)](#-기술-스택-tech-stack)
5. [프로젝트 디렉토리 구조](#-프로젝트-디렉토리-구조)
6. [👨‍💻 나의 역할 및 기여도 (Key Contributions)](#-나의-역할-및-기여도-key-contributions)
7. [🛠️ 핵심 트러블슈팅 경험](#-핵심-트러블슈팅-경험)
8. [시작 가이드 (Getting Started)](#-시작-가이드-getting-started)
9. [결과 및 배운 점](#-결과-및-배운-점)

---

## 📖 프로젝트 개요

### 1. 배경 및 필요성
- **재활용 수거의 한계**: 재활용 가능 자원(특히 플라스틱)이라도 음식물이나 이물질로 **오염된 경우 실제로는 재활용되지 못하고 전량 소각 또는 매립**되는 환경적 문제가 지속되고 있습니다.
- **분리수거 오류 빈발**: 일반 쓰레기, 캔, 플라스틱의 혼합 배출과 오염 플라스틱의 무분별한 투입을 방지할 수 있는 자동화된 분류 솔루션의 필요성이 대두되었습니다.

### 2. 프로젝트 목표
- **2-Stage 딥러닝 모델**을 라즈베리파이 엣지 환경에 탑재하여 객체 감지(1단계)와 플라스틱 오염도 판별(2단계)을 실시간으로 수행.
- 인식 결과에 따라 **아두이노 기반 5축 서보 게이트**를 동작시켜 쓰레기를 물리적으로 자동 분류.
- **초음파 센서**로 적재량을 상시 모니터링하여 넘침을 사전에 방지하는 스마트 분리수거함 구축.

---

## ✨ 핵심 기능

1. **실시간 쓰레기 객체 검출 (YOLOv8 TFLite)**
   - 카메라에 포착된 쓰레기를 실시간으로 탐지하고 바운딩 박스 생성
   - 인식 대상: **일반 쓰레기(General), 캔(Can), 플라스틱(Plastic)** 3대 카테고리 매핑

2. **2단계 정밀 오염도 판별 (EfficientNet-B0 TFLite)**
   - 플라스틱 객체가 감지되면 해당 영역(ROI)만 정밀 크롭하여 2차 신경망으로 전달
   - 플라스틱 표면의 이물질/오염 상태를 판별하여 **CLEAN(재활용 가능)** vs **DIRTY(오염되어 재활용 불가)**로 세부 분류

3. **물리적 자동 분류 메커니즘 (Arduino & Servo Gate)**
   - 판별된 쓰레기 종류에 맞춰 전용 투입 게이트를 개방하고 슬라이딩 도어를 순차 구동
   - 오염된 플라스틱의 경우 재활용함 투입을 차단하여 자원 순환의 순도를 극대화

4. **스마트 적재량 모니터링 및 만적 경고**
   - 초음파 거리 센서를 통해 쓰레기통 내부 여유 공간을 주기적으로 측정
   - 적재 한계선(17cm) 도달 시 RED LED 경고등 점등

---

## 🏗️ 시스템 아키텍처 및 파이프라인

### 1. 전체 하드웨어 & 소프트웨어 아키텍처
```mermaid
graph TD
    subgraph EdgeDevice["Raspberry Pi 4 (AI Edge Device)"]
        Cam["Picamera2 (640x480 Video Stream)"] --> Pre["Frame Preprocessing & Skipping"]
        Pre --> YOLO["1단계: YOLOv8 Object Detection (best.tflite)"]
        YOLO -->|일반 쓰레기| GenMsg["'G,Y' 패킷 생성"]
        YOLO -->|캔| CanMsg["'C,Y' 패킷 생성"]
        YOLO -->|플라스틱 감지| Crop["ROI Bounding Box Crop (224x224)"]
        Crop --> EffNet["2단계: EfficientNet-B0 (contamination_effnet.tflite)"]
        EffNet -->|깨끗한 플라스틱| CleanMsg["'P,Y' 패킷 생성"]
        EffNet -->|오염된 플라스틱| DirtyMsg["'P,N' 패킷 생성"]
        
        GenMsg --> SerialOut["USB-to-Serial 송신 (/dev/ttyUSB0)"]
        CanMsg --> SerialOut
        CleanMsg --> SerialOut
        DirtyMsg --> SerialOut
    end

    subgraph MCU["Arduino Uno R3 (Actuator & Sensor Control)"]
        SerialIn["Serial.readStringUntil('\\n')"] --> ProtocolParser["패킷 파싱 ('G','P','C', 오염 여부)"]
        
        ProtocolParser -->|'G'| GateG["일반 쓰레기 게이트 (Servo D3, D5)"]
        ProtocolParser -->|'P,Y'| GateP["플라스틱 게이트 (Servo D6, D9)"]
        ProtocolParser -->|'C'| DoorCan["슬라이딩 도어 직접 투입"]
        ProtocolParser -->|'P,N'| Reject["오염 플라스틱 분리/경고"]
        
        GateG --> SlideDoor["슬라이딩 도어 구동 (Servo D11)"]
        GateP --> SlideDoor
        DoorCan --> SlideDoor

        Ultra["HC-SR04 초음파 센서 (Trig D4, Echo D2)"] --> DistCheck["거리 측정 (Threshold 17cm)"]
        DistCheck --> LED["만적 경고 RED LED (D12)"]
    end

    SerialOut ===|USB-Serial Data Cable (9600 bps)| SerialIn
```

### 2. 2-Stage 딥러닝 인식 파이프라인
```
[ Picamera2 영상 입력 ]
        │
        ▼
[ 1단계: YOLOv8 경량화 검출 ] ── (Can / General / Plastic 분류)
        │
        ├─ Can ─────────► [C,Y] 패킷 전송
        ├─ General ─────► [G,Y] 패킷 전송
        └─ Plastic
             │ (Bounding Box ROI Crop)
             ▼
[ 2단계: EfficientNet-B0 오염도 판별 ]
             ├─ Clean (dirty_prob ≤ 0.5) ─► [P,Y] 패킷 전송
             └─ Dirty (dirty_prob > 0.5) ─► [P,N] 패킷 전송
```

---

## 🛠 기술 스택 (Tech Stack)

| 영역 | 기술 및 도구 | 활용 목적 |
|---|---|---|
| **AI / Deep Learning** | `YOLOv8` (Ultralytics), `TensorFlow`, `Keras` | 객체 검출 및 전이학습(Transfer Learning) 기반 오염도 분류 모델 학습 |
| **Model Optimization** | `TensorFlow Lite (TFLite)` | 라즈베리파이 엣지 환경 구동을 위한 모델 경량화 및 FP32/INT 양자화 변환 |
| **Edge Vision & Logic** | `Python 3`, `OpenCV`, `Picamera2`, `NumPy` | 실시간 영상 스트리밍 처리, ROI 크롭, 프레임 스킵 최적화 |
| **Hardware & Firmware** | `Arduino Uno R3`, `C/C++ (Arduino IDE)` | 서보모터 5축 제어, 초음파 거리 센서(HC-SR04), 상태 LED 제어 |
| **Communication** | `PySerial`, `UART over USB (/dev/ttyUSB0)` | 라즈베리파이 ↔ 아두이노 간 9600 bps 시리얼 통신 파이프라인 |

---

## 📂 프로젝트 디렉토리 구조

```text
AI 융합 캡스톤 디자인 최종/
├── README.md                      # [본 문서] 프로젝트 전체 통합 포트폴리오 문서
├── ai/                            # AI 비전 및 엣지 컴퓨팅 서브시스템
│   ├── inference/
│   │   └── detect_live.py         # 라즈베리파이 실시간 2-Stage 비전 추론 및 아두이노 제어
│   ├── models/
│   │   ├── best.tflite            # 1단계 쓰레기 객체 검출 YOLOv8 TFLite 모델
│   │   └── contamination_effnet.tflite # 2단계 플라스틱 오염도 판별 EfficientNet TFLite 모델
│   └── train/
│       ├── train_yolo.py          # YOLOv8n 객체 검출 모델 학습 스크립트
│       └── train_effnet.py        # EfficientNet-B0 기반 오염도 분류 모델 학습 및 TFLite 변환
└── arduino/                       # 아두이노 하드웨어 제어 서브시스템
    ├── README.md                  # 아두이노 회로 핀 맵, 제어 로직, UART 트러블슈팅 상세
    └── project/
        └── project.ino            # 아두이노 메인 제어 펌웨어 (서보 5축, 초음파, LED)
```

---

## 👨‍💻 나의 역할 및 기여도 (Key Contributions)

본 프로젝트에서 **학습 이미지 데이터 엔지니어링**과 **아두이노 펌웨어 및 하드웨어 제어 시스템 전반**을 전담하여 성공적인 프로젝트 완성을 이끌었습니다.

### 1. 학습 이미지 데이터 분류 및 데이터셋 엔지니어링
- **다중 클래스 이미지 데이터 정제 및 라벨링**:
  - 일반 쓰레기, 캔, 플라스틱 등 실제 생활 환경에서 발생할 수 있는 다양한 폐기물 이미지 수집
  - YOLOv8 포맷에 맞는 바운딩 박스 라벨링 및 클래스 불균형(Class Imbalance) 해소
- **오염도 판별 전용 데이터셋 구축 (Clean vs Dirty)**:
  - 플라스틱 재활용의 핵심 난제인 '오염도'를 기계가 학습할 수 있도록, 세척된 투명 플라스틱(Clean)과 음식물/양념/이물질이 묻은 플라스틱(Dirty)을 명확한 기준으로 분류 및 정제
  - 데이터 증강(Data Augmentation: 회전, 밝기 조정, 반전)을 적용하여 조명 변화 및 각도에 강인한 학습 데이터셋 구축 (`plastic_contamination`)

### 2. 아두이노 펌웨어 개발 및 메카트로닉스 제어 (100% 기여)
- **5축 서보모터 정밀 구동 시퀀스 설계**:
  - 일반 쓰레기 게이트 2개, 플라스틱 게이트 2개, 슬라이딩 도어 1개의 유기적 동작 타이밍(`delay` 및 `write`) 조율
  - 모터의 기구적 간섭을 방지하기 위해 게이트 개방 → 슬라이딩 도어 투입(7초) → 게이트 폐쇄(3초) 순차 제어 알고리즘 구현
- **초음파 센서 기반 실시간 적재량 측정 알고리즘 개발**:
  - `pulseIn()` 타임아웃(30ms) 처리를 적용하여 센서 이상으로 인한 펌웨어 블로킹(무한 루프) 방지
  - 임계치(17cm) 이하 감지 시 RED LED를 점등하는 실시간 시각 피드백 시스템 구현
- **시리얼 패킷 파서 구현**:
  - 라즈베리파이로부터 유입되는 `[종류],[오염여부]\n` 형태의 문자열을 안정적으로 수신하고 파싱하는 펌웨어 로직 작성

### 3. 하드웨어 인터페이스 트러블슈팅 및 통신 안정화 주도
- 초기 점퍼 케이블 UART 직결 시 발생한 **전압 레벨 불일치 및 모터 역기전력으로 인한 스파크(쇼트) 현상을 분석**
- 신속하게 **USB-Serial 직결 아키텍처로 설계를 변경**하여 하드웨어 파손 방지 및 100% 패킷 무손실 통신 달성 ([상세 트러블슈팅 참조](#-핵심-트러블슈팅-경험))

---

## 🛠️ 핵심 트러블슈팅 경험

### [하드웨어/통신] 점퍼 와이어 UART 직결 시 쇼트/스파크 문제 해결
- **문제 현상**: 라즈베리파이 GPIO(3.3V)와 아두이노 하드웨어 시리얼(5V)을 점퍼선으로 직결했을 때, 다수의 서보모터가 동시 구동되면서 발생한 유도성 역기전력과 접지 전위 불안정으로 인해 케이블 연결부에서 스파크(쇼트)가 발생하고 시리얼 포트가 셧다운되는 치명적 하드웨어 이슈 발생.
- **원인 분석**: 3.3V와 5V 간 로직 레벨 불일치 + 레벨 시프터 부재 + 모터 기동 시 발생하는 서지 전류의 신호선 유입.
- **해결 방안**: 점퍼선 연결을 전면 중단하고 **USB Type-A to B 데이터 케이블을 통한 USB-Serial 통신(`/dev/ttyUSB0`)**으로 전환. 아두이노 내장 USB 컨트롤러의 보호 회로와 차폐 케이블을 활용하여 노이즈와 과전류를 완벽히 격리.
- **결과**: 장시간 연속 작동 시에도 스파크 및 통신 끊김 없이 신뢰성 100%의 양방향 통신 확보. (자세한 분석 내용은 [아두이노 README](file:///d:/auto_trash/AI%20%EC%9C%B5%ED%95%A9%20%EC%BA%A1%EC%8A%A4%ED%86%A4%20%EB%94%94%EC%9E%90%EC%9D%B8%20%EC%B5%9C%EC%A2%85/arduino/README.md)에 상세히 기술)

### [딥러닝 추론 최적화] 라즈베리파이 엣지 환경의 추론 지연(Latency) 개선
- **문제 현상**: 라즈베리파이 단일 보드에서 고해상도 웹캠 스트림과 2개의 딥러닝 모델(YOLO + EfficientNet)을 매 프레임 연속 구동 시 심각한 프레임 드랍(FPS 저하) 및 발열 발생.
- **해결 방안**:
  1. `FRAME_SKIP = 5`를 도입하여 5프레임마다 1회 추론하고 이전 결과를 캐싱하여 렌더링.
  2. 플라스틱이 감지된 경우에만 2단계 EfficientNet을 조건부 트리거하도록 파이프라인 최적화.
  3. 모든 모델을 TensorFlow Lite(FP32)로 경량 변환하고 `num_threads=2` 멀티스레딩 추론 적용.
- **결과**: 영상 끊김 없는 부드러운 실시간 프리뷰와 안정적인 분류 반응 속도 확보.

---

## 🚀 시작 가이드 (Getting Started)

### 1. 하드웨어 설정 (Arduino)
1. [아두이노 핀 맵](file:///d:/auto_trash/AI%20%EC%9C%B5%ED%95%A9%20%EC%BA%A1%EC%8A%A4%ED%86%A4%20%EB%94%94%EC%9E%90%EC%9D%B8%20%EC%B5%9C%EC%A2%85/arduino/README.md)에 맞추어 서보모터 5개, 초음파 센서, LED 결선.
2. Arduino IDE에서 [project.ino](file:///d:/auto_trash/AI%20%EC%9C%B5%ED%95%A9%20%EC%BA%A1%EC%8A%A4%ED%86%A4%20%EB%94%94%EC%9E%90%EC%9D%B8%20%EC%B5%9C%EC%A2%85/arduino/project/project.ino) 열기.
3. 아두이노 Uno에 펌웨어 업로드.
4. USB 케이블로 라즈베리파이와 아두이노를 직접 연결.

### 2. 라즈베리파이 실시간 추론 실행
```bash
# 필수 의존성 설치
pip install opencv-python numpy pyserial tflite-runtime

# 실시간 감지 및 자동 분류 구동
python ai/inference/detect_live.py
```

### 3. AI 모델 재학습 (선택 사항)
```bash
# 1단계: YOLOv8 쓰레기 객체 검출 모델 학습
python ai/train/train_yolo.py

# 2단계: EfficientNet-B0 플라스틱 오염도 분류 모델 학습 및 TFLite 변환
python ai/train/train_effnet.py
```

---

## 📈 결과 및 배운 점

1. **AI와 임베디드 하드웨어의 유기적 결합 경험**
   - 딥러닝 비전 알고리즘이 화면상의 박스를 그리는 것에 그치지 않고, 물리적인 액추에이터를 직접 제어하여 현실 세계의 환경 문제를 해결하는 end-to-end 시스템을 완성했습니다.
2. **현장 트러블슈팅 능력 배양**
   - 회로 구성 시 이론상 가능한 결선(GPIO UART 직결)이라도 모터 부하, 역기전력, 전압 레벨 차이 등 실제 물리적 환경에서 발생하는 변수를 예측하고, 이를 USB-Serial과 같은 안정적인 인터페이스로 빠르게 우회 및 해결하는 실무 엔지니어링 역량을 함양했습니다.
3. **데이터 중심 AI(Data-Centric AI)의 중요성 확인**
   - 플라스틱 오염도 분류 성능을 높이기 위해 단순히 모델 구조를 복잡하게 만드는 것보다, 'Clean'과 'Dirty'의 명확한 이미지 데이터셋을 정제하고 증강하는 데이터 엔지니어링 작업이 모델의 실질적 정확도에 결정적임을 체감했습니다.
