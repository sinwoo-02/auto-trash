from ultralytics import YOLO

def main():
    print("YOLOv8 학습을 시작합니다...")

    DEVICE = 0 # GPU

    # 모델 로드 시 장치 지정
    model = YOLO('yolov8n.pt')
    model.to(DEVICE) 

    # 2. 학습 실행
    results = model.train(data='./trash_dataset_yolo/data.yaml',
                          epochs=50,
                          imgsz=640,
                          task='detect')

    print("="*20)
    print(f"학습 완료! 결과는 {results.save_dir} 폴더에 저장됩니다.")
    print("best.pt 파일이 생성되었는지 확인하세요.")
    print("="*20)

if __name__ == '__main__':
    main()