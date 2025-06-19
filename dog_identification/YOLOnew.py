import cv2
import torch
from PIL import Image
import os
import sys

# Add the parent directory to the Python path to allow imports from other folders
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from features.artificial_intelligence import get_predictor

# --- Constants ---
WINDOW_NAME = "Dog and Human Detection"
WEBCAM_INDEX = 0
CONFIDENCE_THRESHOLD = 0.4

def initialize_models():
    """Loads the YOLOv5 and DogBreedPredictor models."""
    try:
        print("Loading Dog Breed Predictor model...")
        predictor = get_predictor()
        if predictor is None:
            raise IOError("Failed to get the DogBreedPredictor instance.")
        print("Dog Breed Predictor model loaded successfully.")

        print("Loading YOLOv5 model...")
        yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        yolo_model.conf = CONFIDENCE_THRESHOLD
        # Filter for 'dog' (index 16) and 'person' (index 0)
        yolo_model.classes = [0, 16]
        print("YOLOv5 model loaded successfully.")
        return yolo_model, predictor

    except Exception as e:
        print(f"FATAL: Failed to initialize models: {e}", file=sys.stderr)
        return None, None

def main():
    """Main function to run the webcam detection application."""

    # --- Step 1: Open the webcam FIRST ---
    # This is to avoid library conflicts that might prevent camera access after
    # loading heavy models like YOLOv5.
    cap = cv2.VideoCapture(WEBCAM_INDEX) # Use default backend
    if not cap.isOpened():
        print(f"FATAL: Cannot open webcam at index {WEBCAM_INDEX}", file=sys.stderr)
        print("Please ensure no other application is using the camera and that it is connected.", file=sys.stderr)
        return

    # --- Step 2: Now, initialize the models ---
    yolo_model, predictor = initialize_models()
    if not all([yolo_model, predictor]):
        cap.release() # Release the camera if models fail to load
        return

    # Explicitly load the model data for the predictor
    try:
        print("Loading DogBreedPredictor model data...")
        predictor.load_model()
        print("DogBreedPredictor model data loaded successfully.")
    except Exception as e:
        print(f"FATAL: Failed to load DogBreedPredictor model: {e}", file=sys.stderr)
        cap.release()
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame, exiting...", file=sys.stderr)
            break

        # Convert frame to RGB for YOLOv5 model
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # YOLOv5 Detection
        results = yolo_model(rgb_frame)
        detections = results.xyxy[0].cpu().numpy()

        for *xyxy, conf, cls in detections:
            x1, y1, x2, y2 = map(int, xyxy)
            label = "Unknown"
            class_name = yolo_model.names[int(cls)]

            if class_name == 'dog':
                dog_img = frame[y1:y2, x1:x2]
                if dog_img.size > 0:
                    try:
                        # Use the correct method for frame data: predict_top_breeds_from_frame
                        top_breeds = predictor.predict_top_breeds_from_frame(dog_img, k=1)
                        if top_breeds and top_breeds[0][0] != 'Undetermined':
                            breed = top_breeds[0][0]
                            label = breed.replace('_', ' ') # Make it readable
                        else:
                            label = "Dog (Unknown Breed)"
                    except Exception as e:
                        print(f"Could not classify dog breed: {e}", file=sys.stderr)
                        label = "Dog (Unknown Breed)"

            elif class_name == 'person':
                label = "Human"

            # Draw bounding box and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            text = f"{label} ({conf:.2f})"
            (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(frame, (x1, y1 - text_height - 10), (x1 + text_width, y1), (0, 255, 0), -1)
            cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        cv2.imshow(WINDOW_NAME, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("Application closed.")

if __name__ == '__main__':
    main()

