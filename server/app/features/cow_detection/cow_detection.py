import numpy as np
import torch
from ultralytics import YOLO


class CowDetection:
    def __init__(self):
        self.model = YOLO("../../detection_models/cow_detection.pt")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def detect(self, frame: np.ndarray) -> None:
        results = self.model.predict(frame, imgsz=640, device=self.device, conf=0.7, iou=0.45, show=False, save=False)
