import time
import math
import cv2
import numpy as np
import pyautogui
import autopy
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

import HandTrackingModule as htm   # your new module

# ----------------------------------------------------------------------
# Helper ----------------------------------------------------------------
def put_text(img, text, loc=(250, 450), color=(0, 255, 255)):
    cv2.putText(img, str(text), loc,
                cv2.FONT_HERSHEY_COMPLEX_SMALL, 3, color, 3)

# ----------------------------------------------------------------------
# Camera & detector setup ----------------------------------------------
wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)            # use 1 if you have a second webcam
cap.set(3, wCam)
cap.set(4, hCam)
if not cap.isOpened():
    raise RuntimeError("Cannot open webcam – check index or permissions.")

detector = htm.HandDetector(max_hands=1,
                            detection_confidence=0.85,
                            tracking_confidence=0.8)

# ----------------------------------------------------------------------
# System‑volume interface ----------------------------------------------
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_,
                             CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
minVol = -63
maxVol = volume.GetVolumeRange()[1]    # usually 0.0

# ----------------------------------------------------------------------
# Constants -------------------------------------------------------------
hmin, hmax = 50, 200                   # hand‑distance range (pixels)
tip_ids = [4, 8, 12, 16, 20]
mode = 'N'                             # N = neutral
active = 0
color = (0, 215, 255)

pyautogui.FAILSAFE = False
pTime = 0

# ----------------------------------------------------------------------
# Main loop -------------------------------------------------------------
while True:
    success, img = cap.read()
    if not success or img is None:
        print("⚠️  Frame grab failed.")
        break

    img = detector.find_hands(img)
    lm_list = detector.find_position(img, draw=False)

    fingers = []
    if lm_list:
        # ---------- Finger state detection ----------------------------
        # Thumb (special case: check x‑axis because thumb is rotated)
        if lm_list[tip_ids[0]].x > lm_list[tip_ids[0] - 1].x:
            fingers.append(1)
        else:
            fingers.append(0)

        # Other four fingers (compare y‑axis)
        for i in range(1, 5):
            if lm_list[tip_ids[i]].y < lm_list[tip_ids[i] - 2].y:
                fingers.append(1)
            else:
                fingers.append(0)

        # ---------- Mode switching ------------------------------------
        if fingers == [0, 0, 0, 0, 0] and not active:
            mode = 'N'
        elif fingers in ([0, 1, 0, 0, 0], [0, 1, 1, 0, 0]) and not active:
            mode, active = 'Scroll', 1
        elif fingers == [1, 1, 0, 0, 0] and not active:
            mode, active = 'Volume', 1
        elif fingers == [1, 1, 1, 1, 1] and not active:
            mode, active = 'Cursor', 1

    # ------------------------------------------------------------------
    # Mode‑specific logic ----------------------------------------------
    if mode == 'Scroll':
        put_text(img, mode)
        cv2.rectangle(img, (200, 410), (245, 460), (255, 255, 255), cv2.FILLED)

        if fingers == [0, 1, 0, 0, 0]:
            put_text(img, 'U', (200, 455), (0, 255, 0))
            pyautogui.scroll(300)
        elif fingers == [0, 1, 1, 0, 0]:
            put_text(img, 'D', (200, 455), (0, 0, 255))
            pyautogui.scroll(-300)
        elif fingers == [0, 0, 0, 0, 0]:
            mode, active = 'N', 0

    elif mode == 'Volume':
        put_text(img, mode)
        if fingers and fingers[-1] == 1:          # pinky up → exit
            mode, active = 'N', 0
        elif lm_list:
            x1, y1 = lm_list[4].x, lm_list[4].y     # thumb tip
            x2, y2 = lm_list[8].x, lm_list[8].y     # index tip
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(img, (x1, y1), 10, color, cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, color, cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), color, 3)
            cv2.circle(img, (cx, cy), 8, color, cv2.FILLED)

            length = math.hypot(x2 - x1, y2 - y1)
            vol = np.interp(length, [hmin, hmax], [minVol, maxVol])
            volume.SetMasterVolumeLevel(vol, None)

            vol_bar = int(np.interp(vol, [minVol, maxVol], [400, 150]))
            vol_per = int(np.interp(vol, [minVol, maxVol], [0, 100]))

            cv2.rectangle(img, (30, 150), (55, 400), (209, 206, 0), 3)
            cv2.rectangle(img, (30, vol_bar), (55, 400), (215, 255, 127), cv2.FILLED)
            cv2.putText(img, f'{vol_per}%', (25, 430),
                        cv2.FONT_HERSHEY_COMPLEX, 0.9, (209, 206, 0), 3)

    elif mode == 'Cursor':
        put_text(img, mode)
        cv2.rectangle(img, (110, 20), (620, 350), (255, 255, 255), 3)

        if fingers[1:] == [0, 0, 0, 0]:            # thumb ignored
            mode, active = 'N', 0
        elif lm_list:
            x1, y1 = lm_list[8].x, lm_list[8].y    # index tip
            screen_w, screen_h = autopy.screen.size()
            X = int(np.interp(x1, [110, 620], [0, screen_w - 1]))
            Y = int(np.interp(y1, [20, 350], [0, screen_h - 1]))
            autopy.mouse.move(X - X % 2, Y - Y % 2)   # snap to even px

            # left‑click if thumb touches index
            if fingers[0] == 0:
                cv2.circle(img, (lm_list[4].x, lm_list[4].y),
                           10, (0, 0, 255), cv2.FILLED)
                pyautogui.click()

    # ------------------------------------------------------------------
    # FPS & display -----------------------------------------------------
    cTime = time.time()
    fps = 1 / max((cTime - pTime), 1e-5)
    pTime = cTime
    cv2.putText(img, f'FPS:{int(fps)}', (480, 50),
                cv2.FONT_ITALIC, 1, (255, 0, 0), 2)

    cv2.imshow('Hand LiveFeed', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

