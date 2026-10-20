import tensorflow as tf
from tensorflow.keras import layers, models
import os

# --- 설정 ---
DATA_DIR = 'plastic_contamination'
IMG_SIZE = (224, 224)
BATCH_SIZE = 32

# 1. 데이터 불러오기
print("데이터를 불러옵니다...")
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR, validation_split=0.2, subset="training", seed=123,
    image_size=IMG_SIZE, batch_size=BATCH_SIZE
)
val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR, validation_split=0.2, subset="validation", seed=123,
    image_size=IMG_SIZE, batch_size=BATCH_SIZE
)

# 2. 성능 최적화
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

# 3. 모델 만들기 (EfficientNetB0)
base_model = tf.keras.applications.EfficientNetB0(
    input_shape=IMG_SIZE + (3,),
    include_top=False,
    weights='imagenet'
)
base_model.trainable = False

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.2),
    layers.Dense(1, activation='sigmoid') # 0: Clean, 1: Dirty
])

model.compile(optimizer='adam',
              loss='binary_crossentropy',
              metrics=['accuracy'])

# 4. 학습 실행
print("EfficientNetB0 학습 시작...")
history = model.fit(train_ds, validation_data=val_ds, epochs=10)

# 5. TFLite 변환
print("TFLite 변환 중...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# 파일 저장
with open('contamination_effnet.tflite', 'wb') as f:
    f.write(tflite_model)

print("완료! 'contamination_effnet.tflite' 파일을 다운로드하세요.")