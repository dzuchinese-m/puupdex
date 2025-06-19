import cv2
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import pickle
from PIL import Image
import numpy as np
import time
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
# ==== LOAD MODEL ====
print("Loading model....")
model_path = os.path.join(parent_dir, "puprecogniser_model\.tsinghua_refined", "dog_breed_mobilenetv2_calibrated.pth")
label_encoder_path = os.path.join(parent_dir, "puprecogniser_model\.tsinghua_refined", "label_encoder.pkl")

# Load label encoder
with open(label_encoder_path, 'rb') as f:
    label_encoder = pickle.load(f)
class_names = label_encoder.classes_

from torchvision.models import mobilenet_v2
model = mobilenet_v2(weights=None)
model.classifier[1] = nn.Linear(model.last_channel, len(class_names))  # adjust for your num classes

checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
if 'model' in checkpoint:
    state_dict = checkpoint['model']
else:
    state_dict = checkpoint

new_state_dict = {}
for k, v in state_dict.items():
    if k == "temperature":
        continue
    if k.startswith('model.'):
        new_state_dict[k[6:]] = v
    else:
        new_state_dict[k] = v

model.load_state_dict(new_state_dict)
model.eval()

# ==== IMAGE TRANSFORM ====
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# ==== OPEN WEBCAM ====
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open webcam")
    exit()

starttime = 0
while True:
    currenttime = time.time()
    fps = 1/(currenttime-starttime)
    starttime = currenttime 

    ret, frame = cap.read()
    if not ret:
        break

    # Preprocess the frame
    img = transform(frame).unsqueeze(0)  # Add batch dimension
    with torch.no_grad():
        output = model(img)
        probs = torch.softmax(output, dim=1)
        conf, pred = torch.max(probs, 1)
        if conf.item() >= 0.5:
            label = f"{class_names[pred]} {conf.item():.2f}"
        else:
            label = "You're not showing me a dog!"

    cv2.putText(frame, label, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    

    cv2.putText(frame, "FPS:" + str(int(fps)), (20,70), cv2.FONT_HERSHEY_PLAIN,2,(0,255,0),2)
    cv2.imshow("MobileNetV2 demo", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:  # 27 is the ESC key
        break

cap.release()
cv2.destroyAllWindows()
