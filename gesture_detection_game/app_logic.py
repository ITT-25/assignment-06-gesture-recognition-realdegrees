import time
import random
from enum import Enum
from recognizer.recognizer import AsyncRecognizer


class GameState(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    GAME_OVER = "game_over"


class GestureGameApp:
    """Main controller for gesture game logic and state."""

    def __init__(self, recognizer: AsyncRecognizer, max_rounds=10, available_gestures=None):
        self.recognizer = recognizer
        self.max_rounds = max_rounds
        self.available_gestures = available_gestures or [
            "rectangle",
            "circle",
            "check",
            "delete_mark",
            "pigtail",
        ]
        self.score = 0
        self.current_round = 0
        self.current_gesture = None
        self.target_template = None
        self.game_state = GameState.WAITING
        self.game_start_time = None
        self.elapsed_time = 0.0
        self._filter_gestures_by_templates()

    def _filter_gestures_by_templates(self):
        template_names = set(
            t[0] for t in [*self.recognizer.templates, *self.recognizer.custom_templates]
        )
        self.available_gestures = list(template_names)

    def start_game(self):
        self.score = 0
        self.current_round = 0
        self.elapsed_time = 0.0
        self.game_start_time = time.time()
        self.game_state = GameState.PLAYING
        self.next_round()

    def next_round(self):
        self.current_round += 1
        if self.current_round > self.max_rounds:
            self.end_game()
            return False
        self._filter_gestures_by_templates()
        self.current_gesture, self.target_template = self._choose_gesture_and_template()
        return True

    def _choose_gesture_and_template(self):
        gesture = random.choice(self.available_gestures)
        templates = [
            t for t in self.recognizer.templates if t[0].startswith(gesture) or gesture in t[0]
        ]
        if not templates:
            return None, None
        _, template_points, _, _ = random.choice(templates)
        return gesture, template_points

    def end_game(self):
        self.elapsed_time = time.time() - self.game_start_time if self.game_start_time else 0.0
        self.game_state = GameState.GAME_OVER

    def check_gesture(self, points):
        prediction = self.recognizer.recognize(points)
        label, _, _, _ = prediction
        success = label.startswith(self.current_gesture) or self.current_gesture in label
        if success:
            self.score += 1
        return prediction, success

    def reset(self):
        self.score = 0
        self.current_round = 0
        self.elapsed_time = 0.0
        self.game_state = GameState.WAITING
        self.game_start_time = None
