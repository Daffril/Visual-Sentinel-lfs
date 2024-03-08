import os
import cv2
from ultralytics import YOLO
from deepface import DeepFace

def draw_text(frame, text, position, font_size=1, thickness=2):
    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (0, 255, 0)
    cv2.putText(frame, text, position, font, font_size, color, thickness, cv2.LINE_AA)

def process_video(video_path, image_path1, image_path2, upload_folder):
    # Load a model for face verification
    face_verification_model = "VGG-Face"
    yolo_model = YOLO('C:\\Users\\LENOVO\\OneDrive\\Desktop\\Visual-Sentinel-main\\face\\yolov8n-face.pt')  # load a custom YOLO model

    cap = cv2.VideoCapture(video_path)
    H, W = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    out = cv2.VideoWriter(os.path.join(upload_folder, 'output_video.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), int(cap.get(cv2.CAP_PROP_FPS)), (W, H))

    frame_count = 0
    person_found = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % 5 == 0:  # Perform face identification every 10th frame
            # Detect faces using YOLO
            results = yolo_model(frame)[0]

            for result in results.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = result

                if score > 0.5:
                    # Extract and compare features for each given face image
                    detected_face = frame[int(y1):int(y2), int(x1):int(x2)]
                    verification_result1 = DeepFace.verify(detected_face, image_path1, model_name=face_verification_model, enforce_detection=False, align=True)
                    verification_result2 = DeepFace.verify(detected_face, image_path2, model_name=face_verification_model, enforce_detection=False, align=True)

                    # Draw bounding box and text
                    color = (0, 255, 0) if verification_result1['verified'] or verification_result2['verified'] else (0, 0, 255)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

                    if verification_result1['verified'] or verification_result2['verified']:
                        text = "Person Found"
                        person_found=True
                        draw_text(frame, text, (int(x1), int(y1) - 10), font_size=1.5, thickness=3)
                    out.write(frame)
        # Write the frame to the output video
        
        frame_count += 1

    cap.release()
    out.release()

    if person_found:
        return 'Person Found'
    else:
        return 'Person Not Found'
