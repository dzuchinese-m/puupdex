from detector import *
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)

folder = os.path.join(parent_dir, "model_data")

def main():
    videoPath = 0 #path or 0 for camera
    configPath = os.path.join(folder, "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt")
    modelPath = os.path.join(folder, "frozen_inference_graph.pb")
    classesPath = os.path.join(folder, "coco.names")

    detector = Detector(videoPath, configPath, modelPath, classesPath)
    detector.onVideo()

if __name__ =='__main__':
    main()