import cv2
import yaml
from ultralytics import YOLO
import time
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)

# Paths (update as needed)
model_path = os.path.join(parent_dir, "model_data", "best.pt")
data_yaml_path = os.path.join(parent_dir, "model_data", "data.yaml")

# Load YOLO model
model = YOLO(model_path)

# Load class names from YAML
with open(data_yaml_path, 'r') as f:
    data_dict = yaml.safe_load(f)
class_names = data_dict['names']

# Open webcam (0 = default camera)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

starttime = 0
while True:
    currenttime = time.time()
    fps = 1/(currenttime-starttime)
    starttime = currenttime  

    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Run YOLO detection on frame
    results = model(frame, verbose=False)

    # results is a list (one for each image/frame)
    # Access first result since only one frame at a time
    result = results[0]

    # Draw boxes and labels on frame
    for box in result.boxes:
        # box.xyxy is tensor with coords: [x1, y1, x2, y2]
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        conf = box.conf[0].item()
        cls = int(box.cls[0].item())
        label = f"{class_names[cls]} {conf:.2f}"

        # Only show box/label if confidence is high enough
        if conf >= 0.5:
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Draw label background
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(frame, (x1, y1 - 20), (x1 + w, y1), (0, 255, 0), -1)
            # Put label text
            cv2.putText(frame, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        # else: do not draw anything for low confidence

    # Show the frame with detections
    cv2.putText(frame, "FPS:" + str(int(fps)), (20,70), cv2.FONT_HERSHEY_PLAIN,2,(0,255,0),2)
    cv2.imshow("YOLO demo", frame)

    # Press 'q' to quit
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:  # 27 is the ESC key
        break

cap.release()
cv2.destroyAllWindows()
