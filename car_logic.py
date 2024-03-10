import os
import time
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import glob
import pandas as pd 

def load_models(): 
    coco_model = YOLO('yolov8x.pt')
    license_plate_detector = YOLO('license.pt')
    return coco_model, license_plate_detector

def initialize_video_capture(video_path):
    cap = cv2.VideoCapture(video_path)
    return cap

def create_video_writer(output_path, fps, width, height):
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
    return out

def detect_vehicles(model, frame, vehicles):
    detections = model(frame)[0]
    detections_ = []
    for detection in detections.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = detection
        if int(class_id) in vehicles:
            detections_.append([x1, y1, x2, y2, score])
    return detections_

def detect_license_plates(license_model, frame, roi):
    license_plates = license_model(roi)[0]
    return license_plates

def process_frames(cap, coco_model, license_plate_detector, output_path, vehicles, out):
    frame_count = 0
    ret = True
    while ret:
        ret, frame = cap.read()
        if ret:
            frame_count += 1
            if frame_count % 30 == 0:  # Skip 15 frames
                detections_ = detect_vehicles(coco_model, frame, vehicles)

                for detection in detections_:
                    xcar1, ycar1, xcar2, ycar2, _ = detection
                    roi_frame = frame[int(ycar1):int(ycar2), int(xcar1): int(xcar2), :]
                    license_plates = detect_license_plates(license_plate_detector, roi_frame, roi_frame)
                    for license_plate in license_plates.boxes.data.tolist():
                        x1, y1, x2, y2, score, class_id = license_plate
                        x1 += xcar1
                        y1 += ycar1
                        x2 += xcar1
                        y2 += ycar1
                        cv2.rectangle(frame, (int(xcar1), int(ycar1)), (int(xcar2), int(ycar2)), (0, 255, 0), 2)
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
                        
                        # Resize the license plate region to 640x640
                        plate_region_resized = cv2.resize(frame[int(y1):int(y2), int(x1):int(x2)], (640, 640))
                        
                        plate_photo_name = f'plate_{frame_count}.jpg'
                        plate_photo_path = os.path.join(output_path, plate_photo_name)
                        cv2.imwrite(plate_photo_path, plate_region_resized)
                out.write(frame)

def process_images(model, input_folder, output_folder):
    image_paths = glob.glob(os.path.join(input_folder, "*.jpg"))
    predictions_list = []
    
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    predictions = model.predict(source="Outputs/detected", conf=0.6,save=True, project=output_folder)
        
    for result in predictions:
            boxes = result.boxes.cpu().numpy()
            for box in boxes:
                cls = int(box.cls[0])
                path = result.path
                class_name = model.names[cls]
                conf = int(box.conf[0] * 100)
                bx = box.xywh.tolist()
                predictions_list.append({'path': path, 'class_name': class_name, 'class_id': cls, 'confidence': conf, 'box_coord': bx})
            
    df = pd.DataFrame(predictions_list)
    df.to_csv('predicted_labels1.csv', index=False)
     
def main(video_path, upload_folder):
    coco_model, license_plate_detector = load_models()
    cap = initialize_video_capture(video_path)
    output_folder_detection = 'Outputs/detected'
    os.makedirs(output_folder_detection, exist_ok=True)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = create_video_writer('Outputs/output_vid_7.mp4', fps, width, height)
    vehicles = [2]
    start_time = time.time()
    process_frames(cap, coco_model, license_plate_detector, output_folder_detection, vehicles,out)
    out.release()
    cap.release()
    model = YOLO("ocr.pt")
    input_folder = "Outputs/detected"
    output_folder_BBX = "Outputs"
    process_images(model, input_folder, output_folder_BBX)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time required: {total_time:.2f} seconds")
