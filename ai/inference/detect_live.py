import os
import cv2
import numpy as np
import time
import serial
from tensorflow.lite.python.interpreter import Interpreter 
from picamera2 import Picamera2 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resolve_model_path(filename):
    candidates = [
        os.path.join(BASE_DIR, '..', 'models', filename),
        os.path.join(BASE_DIR, filename),
        filename
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return filename

YOLO_PATH = resolve_model_path('best.tflite')
CLS_PATH = resolve_model_path('contamination_effnet.tflite')  

ID_TO_GROUP = {
    0: 'plastic', 1: 'plastic',              
    2: 'can', 3: 'can', 4: 'can', 5: 'can',  
    6: 'general', 7: 'general', 8: 'general' 
}

SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600
CONF_THRESHOLD = 0.5

FRAME_SKIP = 5

def main():
    print(">> Connecting to Arduino...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        ser.flush()
        print(f">> Arduino connected on {SERIAL_PORT}")
    except Exception as e:
        print(f"!! Serial connection failed: {e}")
        ser = None

    print(">> Initializing Picamera2...")
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    
    yolo_interpreter = Interpreter(model_path=YOLO_PATH, num_threads=2)
    yolo_interpreter.allocate_tensors()
    y_input = yolo_interpreter.get_input_details()
    y_output = yolo_interpreter.get_output_details()
    
    cls_interpreter = Interpreter(model_path=CLS_PATH, num_threads=2)
    cls_interpreter.allocate_tensors()
    c_input = cls_interpreter.get_input_details()
    c_output = cls_interpreter.get_output_details()

    frame_count = 0
    last_boxes = []
    last_labels = []
    last_colors = []

    try:
        while True:
            frame = picam2.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            frame_to_show = frame.copy()

            if frame_count % FRAME_SKIP == 0:
                last_boxes = []
                last_labels = []
                last_colors = []
                
                detected = False 
                message = ""     

                y_w, y_h = 640, 640
                img_yolo = cv2.resize(frame, (y_w, y_h))
                input_data = np.expand_dims(img_yolo, axis=0).astype(np.float32) / 255.0

                yolo_interpreter.set_tensor(y_input[0]['index'], input_data)
                yolo_interpreter.invoke()
                output_data = yolo_interpreter.get_tensor(y_output[0]['index'])[0].T

                for row in output_data:
                    conf = np.max(row[4:])
                    
                    if conf > CONF_THRESHOLD:
                        raw_id = np.argmax(row[4:])
                        group_name = ID_TO_GROUP.get(raw_id, "unknown")
                        
                        cx, cy, w, h = row[0:4]
                        ih, iw, _ = frame.shape
                        x1 = int((cx - w/2) * iw)
                        y1 = int((cy - h/2) * ih)
                        x2 = int((cx + w/2) * iw)
                        y2 = int((cy + h/2) * ih)
                        
                        box = (x1, y1, x2, y2)
                        
                        label_text = f"{group_name} ({conf:.2f})"
                        box_color = (0, 255, 0) 

                        if group_name == 'plastic': 
                            w_box = x2 - x1
                            h_box = y2 - y1
                            x_crop = int(max(0, x1))
                            y_crop = int(max(0, y1))
                            
                            roi = frame[y_crop : y_crop + h_box, x_crop : x_crop + w_box]
                            
                            if roi.size > 0:
                                roi_resized = cv2.resize(roi, (224, 224))
                                roi_data = np.expand_dims(roi_resized, axis=0).astype(np.float32)
                                
                                cls_interpreter.set_tensor(c_input[0]['index'], roi_data)
                                cls_interpreter.invoke()
                                dirty_prob = cls_interpreter.get_tensor(c_output[0]['index'])[0][0]
                                
                                if dirty_prob > 0.5:
                                    label_text = f"DIRTY ({dirty_prob:.2f})"
                                    box_color = (0, 0, 255) 
                                    message = "P,N" 
                                else:
                                    label_text = f"CLEAN ({1-dirty_prob:.2f})"
                                    box_color = (255, 0, 0) 
                                    message = "P,Y" 
                            else:
                                continue 

                        elif group_name == 'can':
                            label_text = "CAN"
                            message = "C,Y"

                        elif group_name == 'general':
                            label_text = "GENERAL"
                            message = "G,Y" 

                        last_boxes.append(box)
                        last_labels.append(label_text)
                        last_colors.append(box_color)

                        if message != "":
                            print(f"\n[Action] {label_text} detected!")
                            print(f">> Sending to Arduino: [{message}]")
                            if ser is not None:
                                try:
                                    ser.write((message + '\n').encode('utf-8'))
                                except Exception as e:
                                    print(f"!! Send Failed: {e}")
                                    ser.close()
                                    ser = None 
                            
                            cv2.rectangle(frame_to_show, (x1, y1), (x2, y2), box_color, 2)
                            cv2.putText(frame_to_show, label_text, (x1, y1-10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
                            cv2.imshow("Smart Trash Can", frame_to_show)
                            cv2.waitKey(1) 

                            print(">> Waiting for 8 seconds...")
                            time.sleep(8) 
                            print(">> Restarting detection loop...")
                            picam2.capture_array() 
                            
                            detected = True
                            break 
            
                if detected:
                    frame_count = 0
                    continue

            for box, label, color in zip(last_boxes, last_labels, last_colors):
                cv2.rectangle(frame_to_show, (box[0], box[1]), (box[2], box[3]), color, 2)
                cv2.putText(frame_to_show, label, (box[0], box[1]-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            cv2.imshow("Smart Trash Can", frame_to_show)
            
            frame_count += 1
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            time.sleep(0.01)

    finally:
        if ser is not None:
            ser.close()
        picam2.stop()
        cv2.destroyAllWindows()
        print("Exiting program.")

if __name__ == "__main__":
    main()