import torch
import torch.nn as nn
from torchvision import models
from torchvision.transforms import v2
from PIL import Image
import pickle
import os
import cv2  # Added for video analysis
import time # Added for frame saving
import numpy as np # Added for array handling

class DogBreedPredictor:
    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.device = None
        self.transforms_eval = None
        self._is_loaded = False

    def load_model(self):
        """Load the model and label encoder once at startup"""
        if self._is_loaded:
            return
            
        print("Loading MobileNetV2 model...")
        
        # Get the directory of the current script and navigate to the parent directory
        current_dir = os.path.dirname(__file__)  # features folder
        parent_dir = os.path.dirname(current_dir)  # puupdex folder
        model_dir = os.path.join(parent_dir, "puprecogniser_model\.tsinghua_refined")

        label_encoder_path = os.path.join(model_dir, "label_encoder.pkl")
        model_path = os.path.join(model_dir, "dog_breed_mobilenetv2_calibrated.pth")
        
        # Load label encoder
        with open(label_encoder_path, "rb") as f: 
            self.label_encoder = pickle.load(f)
        num_classes = len(self.label_encoder.classes_)

        # Setup device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model
        self.model = models.mobilenet_v2(weights=None)
        self.model.classifier[1] = nn.Linear(self.model.last_channel, num_classes)

        checkpoint = torch.load(model_path, map_location=self.device)
        if 'model' in checkpoint:
            state_dict = checkpoint['model']
        else:
            state_dict = checkpoint
        clean_state_dict = {}
        for k, v in state_dict.items():
            if k == "temperature":
                continue
            if k.startswith("model."):
                clean_state_dict[k[6:]] = v
            else:
                clean_state_dict[k] = v
        self.model.load_state_dict(clean_state_dict)
        self.model = self.model.to(self.device)
        self.model.eval()

        # Setup transforms
        self.transforms_eval = v2.Compose([
            v2.ToImage(), # Convert numpy array to tensor
            v2.Resize(size=(256, 256)),  # Resize to 256x256
            v2.CenterCrop(size=(224, 224)),
            v2.ToDtype(torch.float32, scale=True),  # Normalize expects float input
            v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        self._is_loaded = True
        print("Model loaded successfully!")
    def preprocess_image(self, image_path):
        """Preprocess the input image for the model."""
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        image = Image.open(image_path).convert("RGB")
        image = self.transforms_eval(image)
        return image.unsqueeze(0).to(self.device) # Add batch dimension
        
    def predict_top_breeds(self, image_path, k=5, confidence_threshold=40.0):
        """Predict the top k dog breeds from the input image.
        If the highest confidence is below threshold, return 'Undetermined'."""
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        image = self.preprocess_image(image_path)

        with torch.no_grad():
            output = self.model(image)
        probabilities = torch.softmax(output, dim=1)
        top_k_confidence, top_k_indices = torch.topk(probabilities, k, dim=1)

        top_k_labels = self.label_encoder.inverse_transform(top_k_indices.cpu().numpy()[0])
        top_k_confidences = top_k_confidence.cpu().numpy()[0] * 100

        # Only return 'Undetermined' if the TOP-1 confidence is below threshold
        if len(top_k_confidences) == 0 or top_k_confidences[0] < confidence_threshold:
            return [("Undetermined", 0.0)]
        
        return list(zip(top_k_labels, top_k_confidences))


# Global instance
_predictor = None

def get_predictor():
    """Get the global predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = DogBreedPredictor()
    return _predictor

def load_model():
    """Load the model (call this at app startup)"""
    predictor = get_predictor()
    predictor.load_model()

def predict_top_breeds(image_path, k=5, confidence_threshold=40.0):
    """Predict the top k dog breeds from the input image."""
    predictor = get_predictor()
    return predictor.predict_top_breeds(image_path, k, confidence_threshold)

def analyze_video_for_breeds(
    video_path, 
    confidence_threshold_object_detection=0.5, 
    confidence_threshold_breed=40.0
):
    """
    Analyzes a video, detects dogs/horses, predicts breeds frame by frame,
    aggregates predictions, and returns the top 5 overall breeds with a representative frame.
    """
    # Load object detection model (SSD MobileNetV3 COCO) and COCO class names
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    model_data_folder = os.path.join(parent_dir, "model_data")

    configPath = os.path.join(model_data_folder, "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt")
    modelPath = os.path.join(model_data_folder, "frozen_inference_graph.pb")
    classesPath = os.path.join(model_data_folder, "coco.names")

    if not all(os.path.exists(p) for p in [configPath, modelPath, classesPath]):
        print(f"Error: Missing object detection model files. Searched in {model_data_folder}")
        return None, None, "Object detector model files missing."

    obj_detector_net = cv2.dnn_DetectionModel(modelPath, configPath)
    obj_detector_net.setInputSize(320, 320)
    obj_detector_net.setInputScale(1.0 / 127.5)
    obj_detector_net.setInputMean((127.5, 127.5, 127.5))
    obj_detector_net.setInputSwapRB(True)

    # Try CUDA backend if available
    if hasattr(cv2, "cuda") and cv2.cuda.getCudaEnabledDeviceCount() > 0:
        try:
            obj_detector_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            obj_detector_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        except Exception:
            pass

    with open(classesPath, "r") as f:
        coco_classes = f.read().strip().split("\n")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file: {video_path}")
        return None, None, "Error opening video file."

    all_predictions_accumulator = {}
    best_frame_for_display = None
    highest_obj_det_confidence_for_frame = 0.0

    processed_frames = 0
    max_frames_to_check = 90
    dog_equivalent_classes = {"dog", "horse"}

    predictor = get_predictor()
    if not predictor._is_loaded:
        predictor.load_model()

    while cap.isOpened() and processed_frames < max_frames_to_check:
        ret, frame = cap.read()
        if not ret:
            break
        processed_frames += 1
        if processed_frames % 5 != 1 and processed_frames > 1:
            continue

        detection_output = obj_detector_net.detect(frame, confThreshold=confidence_threshold_object_detection)
        try:
            class_ids, confidences, bbox = detection_output
        except ValueError:
            continue

        if len(class_ids) > 0:
            for i, class_id_scalar in enumerate(class_ids.flatten()):
                class_id = int(class_id_scalar)
                if class_id < 0 or class_id >= len(coco_classes):
                    continue
                detected_class_name = coco_classes[class_id]
                object_confidence_val = confidences.flatten()[i]
                if detected_class_name in dog_equivalent_classes:
                    current_bbox = bbox[i]
                    x, y, w, h = current_bbox
                    padding = int(min(w, h) * 0.15)
                    x_pad, y_pad = max(0, x - padding), max(0, y - padding)
                    w_pad = min(frame.shape[1] - x_pad, w + 2 * padding)
                    h_pad = min(frame.shape[0] - y_pad, h + 2 * padding)
                    if w_pad <= 0 or h_pad <= 0:
                        continue
                    cropped_object = frame[y_pad : y_pad + h_pad, x_pad : x_pad + w_pad]
                    if cropped_object.size == 0:
                        continue
                    current_breed_predictions_for_frame = predictor.predict_top_breeds_from_frame(
                        cropped_object, k=5, confidence_threshold=confidence_threshold_breed
                    )
                    if current_breed_predictions_for_frame and \
                       current_breed_predictions_for_frame[0][0] not in ["Undetermined", "Error processing predictions (topk)"]:
                        for pred_breed, pred_conf in current_breed_predictions_for_frame:
                            if pred_breed not in ["Undetermined", "Error processing predictions (topk)"]:
                                all_predictions_accumulator.setdefault(pred_breed, []).append(pred_conf)
                        if object_confidence_val > highest_obj_det_confidence_for_frame:
                            highest_obj_det_confidence_for_frame = object_confidence_val
                            best_frame_for_display = frame.copy()
    cap.release()

    # --- Aggregation of predictions ---
    final_aggregated_predictions = None
    error_to_return = None

    if not all_predictions_accumulator:
        final_aggregated_predictions = [("Undetermined", 0.0)]
        if best_frame_for_display is None:
            error_to_return = "No dog found in video."
        else:
            error_to_return = "No breeds identified with sufficient confidence."
    else:
        aggregated_breed_confidences = []
        for breed, conf_list in all_predictions_accumulator.items():
            if conf_list:
                avg_conf = sum(conf_list) / len(conf_list)
                aggregated_breed_confidences.append((breed, avg_conf))
        if aggregated_breed_confidences:
            aggregated_breed_confidences.sort(key=lambda x: x[1], reverse=True)
            final_aggregated_predictions = aggregated_breed_confidences[:5]
        else:
            final_aggregated_predictions = [("Undetermined", 0.0)]
            error_to_return = "Aggregation resulted in no valid breeds."

    # --- Add "selected" key to predictions for UI card gap ---
    def add_selected_flag(predictions):
        if not predictions:
            return []
        result = []
        for idx, (breed, conf) in enumerate(predictions):
            result.append({
                "breed": breed,
                "confidence": conf,
                "selected": idx == 0  # Only the top prediction is selected
            })
        return result

    final_aggregated_predictions = add_selected_flag(final_aggregated_predictions)

    saved_frame_path = None
    if best_frame_for_display is not None:
        try:
            temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp_frames")
            os.makedirs(temp_dir, exist_ok=True)
            timestamp = int(time.time() * 1000)
            saved_frame_path = os.path.join(temp_dir, f"best_frame_{timestamp}.png")
            cv2.imwrite(saved_frame_path, best_frame_for_display)
        except Exception as e_save:
            if not error_to_return:
                error_to_return = f"Error saving frame: {e_save}"
            saved_frame_path = None
    else:
        if final_aggregated_predictions and final_aggregated_predictions[0][0] == "Undetermined" and not all_predictions_accumulator:
            if not error_to_return:
                error_to_return = "No dog found in video to select a representative frame."

    if final_aggregated_predictions is None:
        final_aggregated_predictions = [("Undetermined", 0.0)]
        if not error_to_return:
            error_to_return = "Failed to determine breeds after aggregation."

    return saved_frame_path, final_aggregated_predictions, error_to_return

# Add this method to DogBreedPredictor for frame-based prediction
def predict_top_breeds_from_frame(self, frame_numpy_array, k=5, confidence_threshold=40.0):
    """Predict the top k dog breeds from the input frame (NumPy HWC BGR array)."""
    if not self._is_loaded:
        raise RuntimeError("DogBreedPredictor model not loaded. Call load_model() first.")
    # Convert BGR to RGB
    from torchvision.transforms import v2
    import torch
    import cv2
    frame_rgb = cv2.cvtColor(frame_numpy_array, cv2.COLOR_BGR2RGB)
    image = self.transforms_eval(frame_rgb)
    image = image.unsqueeze(0).to(self.device)
    with torch.no_grad():
        output = self.model(image)
    probabilities = torch.softmax(output, dim=1)
    top_k_confidence, top_k_indices = torch.topk(probabilities, k, dim=1)
    top_k_labels = self.label_encoder.inverse_transform(top_k_indices.cpu().numpy()[0])
    top_k_confidences = top_k_confidence.cpu().numpy()[0] * 100
    if len(top_k_confidences) == 0 or top_k_confidences[0] < confidence_threshold:
        return [("Undetermined", 0.0)]
    return list(zip(top_k_labels, top_k_confidences))

DogBreedPredictor.predict_top_breeds_from_frame = predict_top_breeds_from_frame
