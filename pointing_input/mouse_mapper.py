from collections import deque
from typing import Optional, Deque, Tuple
from pynput.mouse import Controller, Button
import tkinter as tk
from pointing_input.hand_detector import HandData

class ThumbTouchState():
    """TypedDict to represent the state of thumb touch detection."""
    def __init__(self, index: bool = False, middle: bool = False):
        self.index = index
        self.middle = middle

class MouseMapper:
    def __init__(self, frame_width: int, frame_height: int):
        self.mouse = Controller()
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.center_x = frame_width // 2
        self.center_y = frame_height // 2
        self.screen_width, self.screen_height = self._get_screen_size()
        self.calibrated = False
        self.position_history: Deque[Tuple[int, int]] = deque(maxlen=5)  # For smoothing
        self.last_set_position: Optional[Tuple[int, int]] = None
        self.touch_state_window: Deque[ThumbTouchState] = deque([ThumbTouchState() for _ in range(5)], maxlen=5)  # Sliding window for smoothing
        self.touch_start: Optional[float] = None

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
        """Set the current index finger position as the new center and lock the current mouse position as anchor."""
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

    def get_smoothed_touch_state(self) -> ThumbTouchState:
        # Compute the dominant (majority) state for each finger in the window
        index_count = sum(state.index for state in self.touch_state_window)
        middle_count = sum(state.middle for state in self.touch_state_window)
        smoothed = ThumbTouchState(
            index=index_count >= 3,  # majority in window of 5
            middle=middle_count >= 3
        )
        return smoothed

    def process(self, left_hand: Optional[HandData], right_hand: Optional[HandData], use_right=True):
        import time
        hand = right_hand if use_right else left_hand
                
        # Index finger is mapped to clicking and holding, Middle finger is mapped to dragging
        index_touching = self.index_thumb_touching(hand) if hand else False
        middle_touching = self.middle_thumb_touching(hand) if hand else False 
        # Update sliding window using deque
        prev_state = self.get_smoothed_touch_state()    
        self.touch_state_window.append(ThumbTouchState(index=index_touching, middle=middle_touching))
        current_state = self.get_smoothed_touch_state()
        now = time.time()
        
        # Movement logic with grace period
        if current_state.index or current_state.middle:
            if self.touch_start is None:
                self.touch_start = now
            if now - self.touch_start >= 0.05: # Only move if touching for at least 70ms to avoid movement when intending to click
                if not self.calibrated:
                    self.calibrate_center(hand)
                self.move_mouse(hand)
        else:
            self.touch_start = None
            self.calibrated = False  # Reset calibration if middle finger is not touching
        
        # Clicking Logic
        # Transition: not touching -> touching
        touch_started = current_state.index and not prev_state.index
        if touch_started:
            self.mouse.press(Button.left)

        # Transition: touching -> not touching
        touch_ended = not current_state.index and prev_state.index
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
        return distance < 0.043
    
    def middle_thumb_touching(self, hand: HandData) -> bool:
        """Check if the middle finger tip is touching the thumb tip."""
        if not hand or len(hand.landmarks) < 13:
            return False
        middle_tip = hand.landmarks[12]
        thumb_tip = hand.landmarks[4]
        dx = middle_tip[0] - thumb_tip[0]
        dy = middle_tip[1] - thumb_tip[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5
        return distance < 0.043
