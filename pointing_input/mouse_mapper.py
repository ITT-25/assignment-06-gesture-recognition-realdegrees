from typing import Optional
from pynput.mouse import Controller
import tkinter as tk
from pointing_input.hand_detector import HandData

class MouseMapper:
    def __init__(self, frame_width: int, frame_height: int):
        self.mouse = Controller()
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.center_x = frame_width // 2
        self.center_y = frame_height // 2
        self.screen_width, self.screen_height = self._get_screen_size()
        self.calibrated = False

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
        index_tip = hand.landmarks[8] if len(hand.landmarks) > 8 else hand.landmarks[-1]
        x_norm, y_norm = index_tip[0], index_tip[1]
        self.center_x = int(x_norm * self.frame_width)
        self.center_y = int(y_norm * self.frame_height)

        self.mouse_anchor = self.mouse.position
        self.calibrated = True

    def move_mouse_to_index(self, hand: HandData):
        """Move the mouse pointer to follow the index finger relative to the calibration center and mouse anchor."""
        if not hand or len(hand.landmarks) < 8 or not hasattr(self, 'mouse_anchor'):
            return  # Not enough landmarks or not calibrated yet
        
        index_tip = hand.landmarks[8] if len(hand.landmarks) > 8 else hand.landmarks[-1]
        x_norm, y_norm = index_tip[0], index_tip[1]
        x = int(x_norm * self.frame_width)
        y = int(y_norm * self.frame_height)
        
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
        self.mouse.position = (screen_x, screen_y)

    def process(self, left_hand: Optional[HandData], right_hand: Optional[HandData], use_right=True):
        hand = right_hand if use_right else left_hand
        if not hand:
            return
        if hand.gesture == "Pointing_Up" and self.is_index_fully_extended(hand):
            if not self.calibrated:
                self.calibrate_center(hand)
            self.move_mouse_to_index(hand)
        else:
            self.calibrated = False
        
    def is_index_fully_extended(self, hand: HandData) -> bool:
        """Check if the index finger is fully extended (tip far from base)."""
        if not hand or len(hand.landmarks) < 9:
            return False
        base = hand.landmarks[5]
        tip = hand.landmarks[8]
        dx = tip[0] - base[0]
        dy = tip[1] - base[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5
        return distance > 0.12
