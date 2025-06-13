import cv2
import numpy as np
import time

np.random.seed(19)

class Detector:
    def __init__(self, videoPath, configPath, modelPath, classesPath):
        self.videoPath = videoPath
        self.configPath = configPath
        self.modelPath = modelPath
        self.classesPath = classesPath

        self.net = cv2.dnn_DetectionModel(self.modelPath, self.configPath)
        self.net.setInputSize(320,320)
        self.net.setInputScale(1.0/127.5)
        self.net.setInputMean((127.5, 127.5, 127.5))
        self.net.setInputSwapRB(True)
        self.readClasses()
    
    def readClasses(self):
        with open(self.classesPath, "r") as f:
            self.classesList = f.read().splitlines()

        self.classesList.insert(0, '__Background__')

        self.colorList = np.random.uniform(low=0, high= 255, size=(len(self.classesList),3))
        print(self.classesList)

    def onVideo(self):
        cap = cv2.VideoCapture(self.videoPath)
        
        if (cap.isOpened()==False):
            print("Error opening video...")
            return
        
        starttime = 0

        (success,image) = cap.read()
        while success:
            currenttime = time.time()
            fps = 1/(currenttime-starttime)
            starttime = currenttime


            classLabelIDs, confidence, bboxs = self.net.detect(image, confThreshold = 0.5)

            bboxs = list(bboxs)
            confidence = list(np.array(confidence).reshape(1,-1)[0]) #fncy way to convert to a list idk y
            confidence = list(map(float,confidence)) #ensure everything is a float

            bboxIdx = cv2.dnn.NMSBoxes(bboxs, confidence, score_threshold=0.5, nms_threshold=0.2)
            if len(bboxIdx) != 0:
                for i in range(0, len(bboxIdx)):
                    index = np.squeeze(bboxIdx[i])
                    bbox = bboxs[index]
                    classConfidence = confidence[index]
                    classLabelID = np.squeeze(classLabelIDs[index])
                    classLabel = self.classesList[classLabelID]
                    classColor = [int(c) for c in self.colorList[classLabelID]]
                    displayText = "{}:{:.2f}".format(classLabel, classConfidence)

                    x,y,w,h = bbox
                    cv2.rectangle(image, (x,y), (x+w,y+h), color=classColor, thickness = 1)
                    cv2.putText(image,displayText, (x,y-10), cv2.FONT_HERSHEY_PLAIN, 1,  classColor, 2)

            cv2.putText(image, "FPS:" + str(int(fps)), (20,70), cv2.FONT_HERSHEY_PLAIN,2,(0,255,0),2)
            cv2.imshow("result",image)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

            (success,image) = cap.read()
        cv2.destroyAllWindows()