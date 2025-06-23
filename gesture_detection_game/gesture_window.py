import time
import pyglet
import numpy as np
from pyglet.window import mouse
from gesture_detection_game.gesture_preview import GesturePreview
from gesture_detection_game.app_logic import GestureGameApp, GameState
import cv2

class GestureGameWindow(pyglet.window.Window):
    def __init__(self, recognizer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = GestureGameApp(recognizer)
        self.stroke_points = np.empty((0, 2), dtype=float)
        self.stroke_times = []
        self.set_mouse_visible(True)
        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.pyglet_image = None
        self.score_label = pyglet.text.Label("", font_size=16, x=10, y=self.height-30, anchor_x='left', anchor_y='top', color=(0, 0, 0, 255))
        self.instruction_label = pyglet.text.Label("", font_size=24, x=self.width//2, y=self.height//2, anchor_x='center', anchor_y='center', color=(0, 0, 0, 255))
        self.timer_label = pyglet.text.Label("Time: 0.00s", font_size=16, x=self.width//2, y=self.height-30, anchor_x='center', anchor_y='top', color=(255, 255, 255, 255))
        self.preview = GesturePreview(self.width - 200, self.height - 180, 180, 120)

    def on_key_press(self, symbol: int, modifiers: int):
        if self.app.game_state == GameState.GAME_OVER:
            if symbol == pyglet.window.key.SPACE:
                self.app.start_game()
            return
        if symbol == pyglet.window.key.SPACE and self.app.game_state == GameState.WAITING:
            self.app.start_game()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if self.app.game_state != GameState.PLAYING:
            return
        if button == mouse.LEFT:
            self.stroke_points = np.empty((0, 2), dtype=float)
            self.stroke_times = [int(time.time() * 1000)]

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if self.app.game_state != GameState.PLAYING:
            return
        if buttons & mouse.LEFT:
            self.stroke_points = np.vstack([self.stroke_points, [x, y]])
            self.stroke_times.append(int(time.time() * 1000))

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if self.app.game_state != GameState.PLAYING:
            return
        if button != mouse.LEFT or len(self.stroke_points) <= 1:
            return
        points_np = self.flip_points(self.stroke_points)
        self.app.check_gesture(points_np)
        self.app.next_round()

    def flip_points(self, points: np.ndarray) -> np.ndarray:
        if points.shape[0] == 0:
            return points
        max_y = np.max(points[:, 1])
        min_y = np.min(points[:, 1])
        flipped_points = points.copy()
        flipped_points[:, 1] = max_y - (flipped_points[:, 1] - min_y)
        return flipped_points

    def update_background(self, frame: np.ndarray):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame_rgb.shape
        image_data = frame_rgb.flatten().tobytes()
        self.pyglet_image = pyglet.image.ImageData(w, h, 'RGB', image_data, pitch=-w*3)

    def on_draw(self):
        self.clear()
        if self.pyglet_image:
            self.pyglet_image.blit(0, 0, width=self.width, height=self.height)
        # Draw current stroke
        if len(self.stroke_points) > 1:
            for i in range(len(self.stroke_points) - 1):
                x1, y1 = self.stroke_points[i]
                x2, y2 = self.stroke_points[i + 1]
                pyglet.shapes.Line(x1, y1, x2, y2, thickness=3, color=(0, 255, 0)).draw()
        # Draw preview
        self.preview.draw(self.app.target_template)
        # Draw top bar and timer if not game over
        light_green = (144, 238, 144, 255)  # light green
        if self.app.game_state != GameState.GAME_OVER and self.app.game_start_time is not None:
            elapsed = time.time() - self.app.game_start_time
            self.timer_label.text = f"Time: {elapsed:.2f}s"
            pyglet.text.Label(self.timer_label.text, font_size=16, x=self.width//2, y=self.height-30, anchor_x='center', anchor_y='top', color=light_green).draw()
        # Draw score and round
        if self.app.game_state != GameState.GAME_OVER:
            round_text = f"Round {self.app.current_round}/{self.app.max_rounds}"
            score_text = f"Score: {self.app.score}"
            pyglet.text.Label(score_text, font_size=18, x=15, y=self.height-10, anchor_x='left', anchor_y='top', color=light_green).draw()
            pyglet.text.Label(round_text, font_size=18, x=self.width//2, y=self.height-10, anchor_x='center', anchor_y='top', color=light_green).draw()
        # Draw game over info
        if self.app.game_state == GameState.GAME_OVER:
            rect_width = self.width * 0.7
            rect_height = 140
            rect_x = self.width // 2 - rect_width // 2 - 80
            rect_y = self.height // 2 - rect_height // 2 + 40
            bg_rect = pyglet.shapes.Rectangle(rect_x, rect_y, rect_width, rect_height, color=(240, 240, 240))
            bg_rect.opacity = 220
            bg_rect.draw()
            center_text = (
                f"Final Score: {self.app.score}/{self.app.max_rounds}\n"
                f"Time: {self.app.elapsed_time:.2f}s\n"
                "Press SPACE to restart"
            )
            pyglet.text.Label(center_text, font_size=28, x=self.width//2, y=self.height//2 + 40, anchor_x='center', anchor_y='center', color=(0, 0, 0, 255), multiline=True, width=self.width * 0.8).draw()
        # Draw start prompt if waiting
        if self.app.game_state == GameState.WAITING:
            pyglet.text.Label(
                "Press SPACE to start",
                font_size=28,
                x=self.width//2,
                y=80,
                anchor_x='center',
                anchor_y='bottom',
                color=light_green
            ).draw()
