import time
import cv2
from threading import Thread, Lock
from math import sqrt

from depth_calc import get_depth_map_from_img
from o_tts import play_distance_beep, play_tts
from obj_detection import get_objects_from_frame, model
import os

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

# Shared state
latest_frame = None
frame_lock = Lock()
running = True

# Distance history
distances = {}


def adjust_time_to_fps(fps: float, seconds: float) -> float:
    """Adjust seconds to be representative of 24fps even if actual FPS differs."""
    if fps <= 0:
        return seconds
    return seconds * (fps / 24.0)


def get_x_distance_from_center(center, box_center):
    """Signed Euclidean distance in X from frame center."""
    dx = box_center[0] - center[0]
    dy = box_center[1] - center[1]
    dist = sqrt(dx * dx + dy * dy)
    return -dist if dx < 0 else dist


def reader_thread(rtsp_url="rtsp://raspberrypi.local:8554/rpicam"):
    """Continuously read frames and overwrite latest_frame."""
    global latest_frame, running
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    # cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)  # If supported
    if not cap.isOpened():
        print("Cannot open camera")
        running = False
        return

    while running:
        ret, frame = cap.read()

        if not ret:
            print("Frame read failed; exiting reader thread.")
            running = False
            break
        with frame_lock:
            latest_frame = frame
    cap.release()


def main():
    global running
    # Start reader
    t = Thread(target=reader_thread, daemon=True)
    t.start()

    prev_time = time.time()
    fps = 0.0
    cv2.namedWindow("Live Feed", cv2.WINDOW_NORMAL)

    try:
        while running:
            # Grab a copy of the most recent frame
            with frame_lock:
                frame = None if latest_frame is None else latest_frame.copy()

            if frame is None:
                continue

            # Resize & center marker
            frame = cv2.resize(frame, (640, 480))
            # Flip the frame horizontally and vertically
            frame = cv2.flip(frame, -1)
            frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
            cv2.drawMarker(
                frame,
                frame_center,
                (0, 255, 0),
                markerType=cv2.MARKER_CROSS,
                markerSize=20,
                thickness=2,
            )

            results = get_objects_from_frame(frame)
            if results and any(r.boxes for r in results):
                depth_map = get_depth_map_from_img(frame)

                # Process detections
                for result in results:
                    for box in result.boxes:
                        conf = float(box.conf[0].cpu().numpy())
                        if conf < 0.5:
                            continue
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        class_id = int(box.cls[0].cpu().numpy())
                        name = model.names[class_id]
                        center = ((x1 + x2) // 2, (y1 + y2) // 2)
                        x_dist = get_x_distance_from_center(frame_center, center)
                        curr_time = time.time()
                        depth = float(depth_map[center[1], center[0]])
                        if depth < 0.1:
                            continue

                        key = f"{name} {box.id}"
                        old = distances.get(key, depth)
                        distances[key] = depth

                        # curr_time = time.time()
                        speed = -(depth - old) / adjust_time_to_fps(
                            fps, curr_time - prev_time
                        )

                        # feedback
                        if speed > 0.5:
                            # play_distance_beep(speed, x_dist, depth)
                            play_distance_beep(speed, x_dist)
                            play_tts(f"{name} approaching")

                        # draw box + label
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        label = f"{name} {conf:.2f} D:{depth:.2f} S:{speed:.2f}"
                        ts = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                        cv2.rectangle(
                            frame,
                            (x1, y1 - ts[1] - 10),
                            (x1 + ts[0], y1),
                            (0, 255, 0),
                            -1,
                        )
                        cv2.putText(
                            frame,
                            label,
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 0, 0),
                            1,
                        )

            # FPS calc & display
            now = time.time()
            fps = 1.0 / (now - prev_time) if now != prev_time else fps
            print(fps)
            prev_time = now
            cv2.putText(
                frame,
                f"FPS: {fps:.2f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Live Feed", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                running = False

    finally:
        running = False
        t.join()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
