from typing import Callable, List, Optional, Tuple
import pyglet
from pyglet.window import mouse
import numpy as np
from recognizer.gesture_ui import GestureSaverUI
from recognizer.recognizer import Recognizer, AsyncRecognizer
from recognizer.gesture_saver import GestureSaver
import click
import time
import cv2


class Stroke:
    def __init__(self, points: List[Tuple[float, float]], times: List[int]):
        self.points = points
        self.times = times
        self.prediction: Optional[Tuple[str,
                                        np.ndarray, np.ndarray, float]] = None

    def to_array(self) -> np.ndarray:
        return np.array(self.points, dtype=float)

    def to_times(self) -> np.ndarray:
        return np.array(self.times, dtype=int)

    def __len__(self) -> int:
        return len(self.points)

    def __repr__(self) -> str:
        return self.prediction[0] if self.prediction and self.prediction[0] else ""

    def reset(self):
        self.points = []
        self.times = []
        self.prediction = None


class DrawingWindow(pyglet.window.Window):
    def __init__(self, recognizer: Recognizer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recognizer = recognizer
        self.stroke_points: np.ndarray = np.empty((0, 2), dtype=float)
        self.stroke_times: List[int] = []
        self.label = pyglet.text.Label("Draw a gesture", font_size=13, x=10,
                                       y=self.height-60, anchor_x='left', anchor_y='top', color=(0, 0, 0, 255))
        self.set_mouse_visible(True)
        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.denorm_template = None  # Store denormalized template for drawing
        self.pyglet_image = None  # Store the converted Pyglet image
        self.current_stroke: Stroke = Stroke([], [])

        # Gesture Saving
        self.gesture_saver = GestureSaver()
        self.save_ui = GestureSaverUI(
            self.gesture_saver, self.recognizer, self,
            window_width=self.width,
            window_height=self.height,
            add_callback=self._add_custom_template,
        )
        self._handle_mouse = False
        self._mouse_x, self._mouse_y = 0, 0

    def _add_custom_template(self):
        label = self.save_ui.get_gesture_name_input()
        self.recognizer.add_custom_template(label, self.current_stroke.points, self.current_stroke.times)

    def run(self, on_update: Optional[Callable[[float], None]] = None):
        """Run the Pyglet application."""
        # Start update interval
        if on_update:
            pyglet.clock.schedule_interval(lambda dt: on_update(dt), 1/30)
        pyglet.app.run()

    def update_background(self, frame: np.ndarray):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame_rgb.shape
        image_data = frame_rgb.flatten().tobytes()
        self.pyglet_image = pyglet.image.ImageData(
            w, h, 'RGB', image_data, pitch=-w*3)

    def on_draw(self):
        self.clear()
        # Draw OpenCV frame if available
        if self.pyglet_image:
            self.pyglet_image.blit(0, 0, width=self.width, height=self.height)
        # Draw current stroke as simple lines between points
        if len(self.stroke_points) > 1:
            for i in range(len(self.stroke_points) - 1):
                x1, y1 = self.stroke_points[i]
                x2, y2 = self.stroke_points[i + 1]
                pyglet.shapes.Line(x1, y1, x2, y2, thickness=3,
                                   color=(0, 255, 0)).draw()
        # Draw denormalized template if available
        if self.denorm_template is not None and len(self.denorm_template) > 1:
            for i in range(len(self.denorm_template) - 1):
                x1, y1 = self.denorm_template[i]
                x2, y2 = self.denorm_template[i + 1]
                pyglet.shapes.Line(x1, y1, x2, y2, thickness=3,
                                   color=(255, 0, 0)).draw()
        self.label.draw()
        self.save_ui.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        # Delegate UI click handling to GestureUI
        handled = self.save_ui.handle_mouse_press(x, y, button, self.save_custom_templates)
        if handled:
            self._handle_mouse = False
            print("Mouse press handled by UI")
            return
        self.stroke_points = np.empty((0, 2), dtype=float)
        self.stroke_times = [int(time.time() * 1000)]
        self.label.text = "Drawing..."
        self.denorm_template = None
        self.current_stroke.reset()
        self._handle_mouse = True
        self._mouse_x, self._mouse_y = x, y

    def save_custom_templates(self, subject: str):
        """Save all custom templates to the recognizer."""
        for label, _, times, points in self.recognizer.custom_templates:
            self.gesture_saver.save_gesture(label, subject, points, times)
        print("Custom templates saved.")

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        # Only allow drawing if not interacting with input or save button
        if self._handle_mouse and buttons & mouse.LEFT:
            self.stroke_points = np.vstack([self.stroke_points, [x, y]])
            self.stroke_times.append(int(time.time() * 1000))
            self._mouse_x, self._mouse_y = x, y

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button != mouse.LEFT or len(self.stroke_points) <= 1 or not self._handle_mouse:
            return
        # Flip Y axis for pyglet (origin is bottom-left, but most gesture datasets use top-left)
        points_np = self.flip_points(self.stroke_points)
        self.current_stroke.prediction = self.recognizer.recognize(points_np)
        label, _, denormalized, confidence = self.current_stroke.prediction
        self.label.text = f"Prediction: {label} (Confidence: {confidence:.2f})"
        if denormalized is not None and len(denormalized) > 0:
            denormalized = self.flip_points(denormalized)
        self.denorm_template = denormalized
        self.current_stroke.points = points_np.copy()
        self.current_stroke.times = self.stroke_times.copy()

        if self.save_ui.get_gesture_name_input() == "":
            self.save_ui.gesture_name_input.set_text(str(self.current_stroke))
        if self.save_ui.autocapture:
            self.recognizer.add_custom_template(
                self.save_ui.get_gesture_name_input(), 
                self.current_stroke.points,
                self.current_stroke.times
            )

    def flip_points(self, points: np.ndarray) -> np.ndarray:
        """Flip Y coordinates to convert from or to Pyglet's coordinate system."""
        if points.shape[0] == 0:
            return points
        max_y = np.max(points[:, 1])
        min_y = np.min(points[:, 1])
        flipped_points = points.copy()
        flipped_points[:, 1] = max_y - (flipped_points[:, 1] - min_y)
        return flipped_points


@click.command()
@click.option("--async-loading", "-a", is_flag=True, help="Load templates asynchronously")
def main(async_loading: bool):
    recognizer_args = {}
    recognizer = AsyncRecognizer(
        **recognizer_args) if async_loading else Recognizer(**recognizer_args)
    window = DrawingWindow(recognizer, width=600,
                           height=400, caption="$1 Recognizer Demo")
    window.run()


if __name__ == "__main__":
    main()
