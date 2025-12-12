import cv2
import torch
import numpy as np
from depth_anything_v2.dpt import DepthAnythingV2

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available() else "cpu"
)

print(f"Using device: {DEVICE} for DepthAnythingV2 model")

model_configs = {
    "vits": {"encoder": "vits", "features": 64, "out_channels": [48, 96, 192, 384]},
    "vitb": {"encoder": "vitb", "features": 128, "out_channels": [96, 192, 384, 768]},
    "vitl": {
        "encoder": "vitl",
        "features": 256,
        "out_channels": [256, 512, 1024, 1024],
    },
}

encoder = "vits"  # or 'vits', 'vitb'
dataset = "hypersim"  # 'hypersim' for indoor model, 'vkitti' for outdoor model
max_depth = 20  # 20 for indoor model, 80 for outdoor model
ckpt_path = f"checkpoints/depth_anything_v2_metric_{dataset}_{encoder}.pth"

model = DepthAnythingV2(**model_configs[encoder], max_depth=max_depth)
ckpt = torch.load(ckpt_path, map_location="cpu")
model.load_state_dict(ckpt)
model.to(DEVICE).eval()

# 2) compile (PyTorch ≥2.0) or jit
try:
    model = torch.compile(model, backend="inductor")
except AttributeError:
    example = torch.randn(1, 3, 240, 320, device=DEVICE).half()
    model = torch.jit.trace(model, example)


def get_depth_map_from_img(img: np.ndarray) -> np.ndarray:
    """Get depth map from an image."""
    with torch.no_grad():
        depth = model.infer_image(img)
    # depth = np.ones((480, 640), dtype=np.float16)
    return depth


# raw_img = cv2.imread("your/image/path")
# depth = model.infer_image(raw_img)  # HxW raw depth map in numpy
