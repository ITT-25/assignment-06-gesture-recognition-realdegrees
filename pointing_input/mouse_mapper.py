from collections import deque
from typing import Optional, Deque, Tuple
from pynput.mouse import Controller, Button
import tkinter as tk
from pointing_input.hand_detector import HandData
import math

class HandState():
    """TypedDict to represent the state of thumb touch detection."""
    def __init__(self, index_thumb_touch: bool = False, index_extended: bool = False):
        self.index_thumb_touch = index_thumb_touch
        self.index_extended = index_extended

class MouseMapper:
    def __init__(self, frame_width: int, frame_height: int):
        self.mouse = Controller()
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.center_x = frame_width // 2
        self.center_y = frame_height // 2
        self.screen_width, self.screen_height = self._get_screen_size()
        self.calibrated = False
        self.position_history: Deque[Tuple[int, int]] = deque(maxlen=5)  # Mouse smoothing
        self.last_set_position: Optional[Tuple[int, int]] = None
        self.touch_state_window: Deque[HandState] = deque([HandState() for _ in range(10)], maxlen=10)  # Input smoothing

    def _get_screen_size(self):
        try:
            root = tk.Tk()
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            return width, height
        except Exception:
            # Fallback
            return 1920, 1080

    def calibrate_center(self, hand: HandData):
        """Set the current palm centroid as the new center and lock the current mouse position as anchor."""
        if not hand or len(hand.landmarks) < 8:
            return
        self.center_x, self.center_y = self.get_centroid(hand)
        self.mouse_anchor = self.mouse.position
        self.calibrated = True
    
    # Hardcoded based on https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer#hand_landmark_model_bundle
    def get_centroid(self, hand: HandData) -> Tuple[int, int]:
        """Calculate the centroid of the wrist and finger base."""
        if not hand or not hasattr(hand, "landmarks") or not hand.landmarks:
            return self.center_x, self.center_y

        indices = [0, 1, 5, 9, 13, 17]
        selected_landmarks = [
            hand.landmarks[i] for i in indices if i < len(hand.landmarks)
        ]
        if not selected_landmarks:
            return self.center_x, self.center_y

        xs = [lm[0] for lm in selected_landmarks]
        ys = [lm[1] for lm in selected_landmarks]
        centroid_x = int(sum(xs) / len(xs) * self.frame_width)
        centroid_y = int(sum(ys) / len(ys) * self.frame_height)
        return centroid_x, centroid_y

    def move_mouse(self, hand: HandData):
        """Move the mouse pointer to follow the index finger relative to the calibration center and mouse anchor."""
        if not hand or len(hand.landmarks) < 8 or not hasattr(self, 'mouse_anchor'):
            return  # Not enough landmarks or not calibrated yet

        x, y = self.get_centroid(hand)
        
        # Calculate delta from calibration center
        rel_x = x - self.center_x
        rel_y = y - self.center_y
        
        # Add delta to mouse anchor
        anchor_x, anchor_y = self.mouse_anchor
        screen_x = int(anchor_x + rel_x * (self.screen_width / self.frame_width))
        screen_y = int(anchor_y + rel_y * (self.screen_height / self.frame_height))
        # Clamp to screen
        screen_x = max(0, min(self.screen_width - 1, screen_x))
        screen_y = max(0, min(self.screen_height - 1, screen_y))

        # Smoothing: add to history and average
        self.position_history.append((screen_x, screen_y))
        avg_x = int(sum(p[0] for p in self.position_history) / len(self.position_history))
        avg_y = int(sum(p[1] for p in self.position_history) / len(self.position_history))
        
        self.mouse.position = (avg_x, avg_y)
        self.last_set_position = (avg_x, avg_y)

    def get_smoothed_touch_state(self) -> HandState:
        # Weighted smoothing: newer states have more weight
        weights = list(range(1, len(self.touch_state_window) + 1))
        total_weight = sum(weights)
        index_score = sum(state.index_thumb_touch * w for state, w in zip(self.touch_state_window, weights))
        middle_score = sum(state.index_extended * w for state, w in zip(self.touch_state_window, weights))
        smoothed = HandState(
            index_thumb_touch=index_score >= total_weight / 2,
            index_extended=middle_score >= total_weight / 2
        )
        return smoothed

    def process(self, left_hand: Optional[HandData], right_hand: Optional[HandData], use_right=True):
        hand = right_hand if use_right else left_hand
                
        # Index finger is mapped to clicking and holding, Middle finger is mapped to dragging
        index_touching = self.index_thumb_touching(hand) if hand else False
        index_extended = self.index_extended(hand) if hand else False 
        # Update sliding window using deque
        prev_state = self.get_smoothed_touch_state()    
        self.touch_state_window.append(HandState(index_thumb_touch=index_touching, index_extended=index_extended))
        current_state = self.get_smoothed_touch_state()
        
        # Movement logic with grace period
        if current_state.index_extended or current_state.index_thumb_touch:
            if not self.calibrated:
                self.calibrate_center(hand)
            self.move_mouse(hand)
        else:
            self.calibrated = False  # Reset calibration if middle finger is not touching
        
        # Clicking Logic
        # Transition: not touching -> touching
        touch_started = current_state.index_thumb_touch and not prev_state.index_thumb_touch
        if touch_started:
            self.mouse.press(Button.left)

        # Transition: touching -> not touching
        touch_ended = not current_state.index_thumb_touch and prev_state.index_thumb_touch
        if touch_ended:
            self.mouse.release(Button.left)

    def index_thumb_touching(self, hand: HandData) -> bool:
        """Check if the index finger is touching the thumb."""
        if not hand or len(hand.landmarks) < 9:
            return False
        index_tip = hand.landmarks[8]
        thumb_tip = hand.landmarks[4]
        dx = index_tip[0] - thumb_tip[0]
        dy = index_tip[1] - thumb_tip[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5
        return distance < 0.045
    
    def index_extended(self, hand: HandData) -> bool:
        """Check if the index finger is extended by comparing angles between its joints."""
        if not hand or len(hand.landmarks) < 9:
            return False
        # Landmarks: 5 (MCP), 6 (PIP), 7 (DIP), 8 (TIP)
        def angle(a, b, c):
            # Returns the angle (in degrees) at point b given three points a-b-c
            ax, ay = a[:2]
            bx, by = b[:2]
            cx, cy = c[:2]
            ab = (ax - bx, ay - by)
            cb = (cx - bx, cy - by)
            dot = ab[0] * cb[0] + ab[1] * cb[1]
            norm_ab = (ab[0] ** 2 + ab[1] ** 2) ** 0.5
            norm_cb = (cb[0] ** 2 + cb[1] ** 2) ** 0.5
            if norm_ab == 0 or norm_cb == 0:
                return 0
            cos_angle = dot / (norm_ab * norm_cb)
            cos_angle = max(-1.0, min(1.0, cos_angle))
            return math.degrees(math.acos(cos_angle))

        mcp = hand.landmarks[5]
        pip = hand.landmarks[6]
        dip = hand.landmarks[7]
        tip = hand.landmarks[8]

        # Angles at PIP and DIP joints
        angle_pip = angle(mcp, pip, dip)
        angle_dip = angle(pip, dip, tip)

        # If both angles are close to 180 degrees, the finger is extended
        return angle_pip > 170 and angle_dip > 170
