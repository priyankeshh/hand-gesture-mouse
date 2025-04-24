from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Union

import cv2
import mediapipe as mp


@dataclass
class Landmark:
    id: int
    x: int
    y: int
    z: Union[float, None] = None  # z is optional


class HandDetector:
    """Detects hands and returns landmark positions."""

    def __init__(
        self,
        static_image_mode: bool = False,
        max_hands: int = 2,
        detection_confidence: float = 0.5,
        tracking_confidence: float = 0.5,
        model_complexity: int = 1,
    ) -> None:
        self.static_image_mode = static_image_mode
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence
        self.model_complexity = model_complexity

        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=self.static_image_mode,
            max_num_hands=self.max_hands,
            model_complexity=self.model_complexity,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence,
        )
        self._mp_draw = mp.solutions.drawing_utils
        self.results = None  # will hold last inference results

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def find_hands(self, image, draw: bool = True):
        """Run hand detection on *image* and optionally draw landmarks."""
        if image is None:
            return image

        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.results = self._hands.process(img_rgb)

        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self._mp_draw.draw_landmarks(
                    image,
                    hand_lms,
                    self._mp_hands.HAND_CONNECTIONS,
                )
        return image

    def find_position(
        self,
        image,
        hand_no: int = 0,
        draw: bool = True,
        color: Tuple[int, int, int] = (255, 0, 255),
        include_z: bool = False,
    ) -> List[Landmark]:
        """Return a list of landmarks for *hand_no* in pixel coordinates."""
        lm_list: List[Landmark] = []
        if not self.results or not self.results.multi_hand_landmarks:
            return lm_list

        if hand_no >= len(self.results.multi_hand_landmarks):
            return lm_list

        h, w = image.shape[:2]
        my_hand = self.results.multi_hand_landmarks[hand_no]
        for idx, lm in enumerate(my_hand.landmark):
            cx, cy = int(lm.x * w), int(lm.y * h)
            cz = round(lm.z, 3) if include_z else None
            lm_list.append(Landmark(idx, cx, cy, cz))
            if draw:
                cv2.circle(image, (cx, cy), 5, color, cv2.FILLED)
        return lm_list


# ----------------------------------------------------------------------
# Stand‑alone demo
# ----------------------------------------------------------------------

def _demo() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam – check index/permissions.")
    detector = HandDetector(max_hands=1)

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to capture frame")
            break

        frame = detector.find_hands(frame)
        lm_list = detector.find_position(frame, include_z=True, draw=False)
        if lm_list:
            # Example: print thumb tip (id=4)
            thumb_tip = next(lm for lm in lm_list if lm.id == 4)
            print(f"Thumb tip → x:{thumb_tip.x} y:{thumb_tip.y} z:{thumb_tip.z}")

        cv2.imshow("Hand Tracking Demo", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    _demo()