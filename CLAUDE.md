# Pi in the sky

This project aims to use on-device models to detect the presence of birds in images taken from a USB webcam attached to a Raspberry Pi v4.

---

This is a Python project, using `uv`.

- The system periodically captures images from a webcam.
- Runs on-device inference only. It should not use cloud services.
- Correctly identifies whether at least one bird is present in the frame.
- Logs detections with timestamp and confidence to a SQLite database.
- For now, I am not interested in species classification.

Use a pretrained object detection model trained on the COCO dataset, and filter detections for the "bird" class only.
