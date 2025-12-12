import cv2
import time

url = "rtsp://raspberrypi.local:8554/rpicam"

# Force UDP and disable buffering
cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

# Set FFmpeg flags to minimize latency
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 1 frame buffer, not the default queue
cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)  # If supported
cap.set(cv2.CAP_PROP_FPS, 15)  # Match camera FPS

fps = 0.0
while True:
    start = time.time()
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow("Low-Latency Stream", frame)
    fps = (fps + (1.0 / (time.time() - start))) / 2
    print(f"FPS: {fps:.2f}")
    if cv2.waitKey(1) == 27:  # ESC to exit
        break

cap.release()
cv2.destroyAllWindows()
