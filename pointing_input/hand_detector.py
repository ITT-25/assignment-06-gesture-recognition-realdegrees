import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from typing import List, Tuple, Optional
import numpy as np
import cv2

class HandData:
    def __init__(self, landmarks: List[Tuple[float, float, float]], gesture: str):
        self.landmarks = landmarks
        self.gesture = gesture

class HandDetector:
    def __init__(self, model_path: str = "pointing_input/gesture_recognizer.task"):
        base_options = python.BaseOptions(model_asset_buffer=open(model_path, "rb").read())
        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            num_hands=2
        )
        self.recognizer = vision.GestureRecognizer.create_from_options(options)

    def detect_landmarks(self, image_frame: np.ndarray) -> Tuple[Optional[HandData], Optional[HandData]]:
        rgb_image = cv2.cvtColor(image_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        result = self.recognizer.recognize(mp_image)

        left_hand: Optional[HandData] = None
        right_hand: Optional[HandData] = None

        if result.gestures and result.hand_landmarks:
            for i in range(len(result.gestures)):
                handedness_label = result.handedness[i][0].category_name  # "Left" or "Right"
                gesture_label = result.gestures[i][0].category_name
                landmarks = [(lm.x, lm.y, lm.z) for lm in result.hand_landmarks[i]]

                hand_data = HandData(landmarks, gesture_label)
                if handedness_label == "Left":
                    left_hand = hand_data
                elif handedness_label == "Right":
                    right_hand = hand_data

        return left_hand, right_hand
