import cv2

# Set desired display size (you can adjust)
dispW = 640
dispH = 480
flip = 2  # 0=none, 1=horizontal, 2=vertical

# GStreamer pipeline string for Pi Camera
camSet = (
    'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 ! '
    f'nvvidconv flip-method={flip} ! video/x-raw, width={dispW}, height={dispH}, format=BGRx ! '
    'videoconvert ! video/x-raw, format=BGR ! appsink'
)

# Open camera
import platform 


def try_open(source, backend=None):
    """Try to open a cv2.VideoCapture with optional backend. Return capture or None."""
    try:
        if backend is not None:
            cap = cv2.VideoCapture(source, backend)
        else:
            cap = cv2.VideoCapture(source)
    except Exception as e:
        print(f" Exception while opening camera source={source!r} backend={backend}: {e}")
        return None

    if cap is not None and cap.isOpened():
        print(f" Opened camera source={source!r} backend={backend}")
        return cap

    # make sure we release a failed capture
    try:
        if cap is not None:
            cap.release()
    except Exception:
        pass
    return None


# 1) Try the provided GStreamer pipeline (use CAP_GSTREAMER if available)
cam = None
if hasattr(cv2, 'CAP_GSTREAMER'):
    cam = try_open(camSet, cv2.CAP_GSTREAMER)
else:
    # Some OpenCV builds still accept the pipeline string without the flag
    cam = try_open(camSet)

# 2) If that failed, try platform-appropriate fallbacks (Windows: DSHOW / MSMF)
if cam is None:
    system = platform.system()
    print(f"GStreamer pipeline didn't open — falling back to native backends for {system}.")

    tried = []
    if system == 'Windows':
        # Try DirectShow and Media Foundation with common device indices
        backends = [getattr(cv2, 'CAP_DSHOW', None), getattr(cv2, 'CAP_MSMF', None)]
        for b in backends:
            if b is None:
                continue
            for idx in range(0, 3):
                tried.append((idx, b))
                cam = try_open(idx, b)
                if cam:
                    break
            if cam:
                break
    else:
        # Try default indices on non-Windows (0..3)
        for idx in range(0, 4):
            tried.append((idx, None))
            cam = try_open(idx)
            if cam:
                break

    if cam is None:
        print("\n❌ Cannot open camera using any tested sources. Tried:")
        for s, b in tried:
            print(f"  - source={s!r} backend={b}")
        print("\nSuggestions:")
        print(" - If you're on Raspberry Pi, enable camera in raspi-config and use the original GStreamer pipeline.")
        print(" - On Windows, ensure your camera works in Camera app and drivers are installed.")
        print(" - Try changing the numeric index (0..3) or different backends (DSHOW / MSMF).")
        print(" - If using a virtual environment, ensure OpenCV was installed with the needed backends (GStreamer on Linux/Pi).")
        exit(1)

while True:
    ret, frame = cam.read()
    if not ret:
        print("⚠️ Frame capture failed.")
        break

    cv2.imshow("Pi Camera Test", frame)

    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
