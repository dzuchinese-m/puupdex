import torch
import torch.nn as nn
from torchvision import models
from torchvision.transforms import v2
from PIL import Image
import pickle
import os


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
        model_dir = os.path.join(parent_dir, "puprecogniser_model\.tsinghua")

        label_encoder_path = os.path.join(model_dir, "label_encoder.pkl")
        model_path = os.path.join(model_dir, "mobilenetv2_tsinghua_raw.pth")
        
        # Load label encoder
        with open(label_encoder_path, "rb") as f: 
            self.label_encoder = pickle.load(f)
        num_classes = len(self.label_encoder.classes_)

        # Setup device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model
        self.model = models.mobilenet_v2(weights=None)
        self.model.classifier[1] = nn.Linear(self.model.last_channel, num_classes)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
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

        # Only accept as dog breed if highest confidence is above threshold
        if top_k_confidences[0] < confidence_threshold:
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
