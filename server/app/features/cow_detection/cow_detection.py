import numpy as np
import torch
from ultralytics import YOLO
import supervision as sv
import cv2


class CowDetection:
    def __init__(self):
        self.model = YOLO("../../detection_models/cow_detection.pt")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def detect(self, frame: np.ndarray) -> None:
        results = self.model.predict(frame, imgsz=640, device=self.device, conf=0.3, iou=0.45, show=False, save=False)

        detections = sv.Detections.from_ultralytics(results[0])

        box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()

        annotated_frame = box_annotator.annotate(scene=frame, detections=detections)
        annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections)

        cv2.imshow("frame", annotated_frame)
        cv2.waitKey(0)
        print(results)
