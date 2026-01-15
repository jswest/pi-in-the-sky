import os
import warnings
from dataclasses import dataclass
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="tensorflow")

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from numpy import ndarray  # noqa: E402

# Try tflite-runtime first (lighter, better ARM support), fall back to tensorflow
try:
    from tflite_runtime.interpreter import Interpreter  # noqa: E402
except ImportError:
    import tensorflow as tf  # noqa: E402
    Interpreter = tf.lite.Interpreter

from pisky.paths import ensure_model_downloaded  # noqa: E402

BIRD_CLASS_ID = 14


@dataclass
class Detection:
    confidence: float
    bbox: tuple[float, float, float, float]  # ymin, xmin, ymax, xmax (normalized)


class BirdDetector:
    def __init__(self, model_path: Path | None = None) -> None:
        if model_path is None:
            model_path = ensure_model_downloaded()
        self.interpreter = Interpreter(model_path=str(model_path))
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def detect(self, image: ndarray, min_confidence: float = 0.33) -> list[Detection]:
        """Detect birds in a 300x300 BGR image. Returns list of detections."""
        # Convert BGR (OpenCV) to RGB (model expects RGB)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_data = np.expand_dims(image_rgb, axis=0).astype(np.uint8)
        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)

        # Run inference
        self.interpreter.invoke()

        # Get outputs
        boxes = self.interpreter.get_tensor(self.output_details[0]["index"])[0]
        classes = self.interpreter.get_tensor(self.output_details[1]["index"])[0]
        scores = self.interpreter.get_tensor(self.output_details[2]["index"])[0]

        # Filter for birds above confidence threshold
        detections = []
        for i, (class_id, score) in enumerate(zip(classes, scores)):
            if int(class_id) == BIRD_CLASS_ID and score >= min_confidence:
                detections.append(Detection(
                    confidence=float(score),
                    bbox=tuple(boxes[i])
                ))

        return detections

    def detect_all(self, image: ndarray, min_confidence: float = 0.5) -> list[tuple[int, float]]:
        """Detect all objects (for debugging). Returns list of (class_id, confidence)."""
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_data = np.expand_dims(image_rgb, axis=0).astype(np.uint8)
        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
        self.interpreter.invoke()

        classes = self.interpreter.get_tensor(self.output_details[1]["index"])[0]
        scores = self.interpreter.get_tensor(self.output_details[2]["index"])[0]

        return [(int(c), float(s)) for c, s in zip(classes, scores) if s >= min_confidence]
