import torch
from ultralytics import YOLO


DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available() else "cpu"
)

print(f"Using device: {DEVICE} for YOLOv8 model")

# Load YOLOv8 model (downloads automatically on first use)
model = YOLO("checkpoints/yolov8n.pt")


def get_objects_from_frame(frame: torch.Tensor) -> list:
    results = model.track(frame, verbose=False, device=DEVICE, persist=True)
    return results
