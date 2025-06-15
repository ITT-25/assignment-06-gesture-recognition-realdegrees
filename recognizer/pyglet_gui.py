from typing import Callable, List, Optional, Set, Tuple
import pyglet
from pyglet.window import mouse
import numpy as np
from recognizer import Recognizer, AsyncRecognizer
import click
from recognizer.gesture_saver import GestureSaver
from recognizer.gesture_ui import GestureSaverUI
import time
import cv2

class DrawingWindow(pyglet.window.Window):
    def __init__(self, recognizer: Recognizer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recognizer = recognizer
        self.stroke_points: List[Tuple[float, float]] = []
        self.stroke_times: List[int] = []
        self.label = pyglet.text.Label("Draw a gesture", font_size=18, x=10, y=self.height-40, anchor_x='left', anchor_y='top', color=(0,0,0,255))
        self.set_mouse_visible(True)
        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.denorm_template = None  # Store denormalized template for drawing
        self.pyglet_image = None  # Store the converted Pyglet image
        
        # Gesture Saving
        self.gesture_saver = GestureSaver()
        self.save_ui = GestureSaverUI(self.gesture_saver)
        self._mouse_buttons: Set[int] = set()
        self._mouse_x, self._mouse_y = 0, 0

    def run(self, on_update: Optional[Callable[[float], None]] = None):
        """Run the Pyglet application."""
        # Start update interval
        def update(dt):
            if on_update:
                on_update(dt)
            self.on_update(dt)
        pyglet.clock.schedule_interval(lambda dt: update(dt), 1/120)
        pyglet.app.run()
        
    def on_update(self, dt: float):
        if len(self.stroke_points) > 0:
            # Only sample if mouse is down (drawing)
            if mouse.LEFT in self._mouse_buttons:
                x, y = self._mouse_x, self._mouse_y
                
                # Only add if position changed (avoid duplicates)
                if (x, y) != self.stroke_points[-1]:
                    self.stroke_points.append((x, y))
                    self.stroke_times.append(int(time.time() * 1000))

    def update_background(self, frame: np.ndarray):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame_rgb.shape
        image_data = frame_rgb.flatten().tobytes()
        self.pyglet_image = pyglet.image.ImageData(w, h, 'RGB', image_data, pitch=-w*3)

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
                pyglet.shapes.Line(x1, y1, x2, y2, thickness=3, color=(0, 255, 0)).draw()
                
        # Draw last stroke if available
        if hasattr(self, 'last_stroke_points') and len(self.last_stroke_points) > 1:
            for i in range(len(self.last_stroke_points) - 1):
                x1, y1 = self.last_stroke_points[i]
                x2, y2 = self.last_stroke_points[i + 1]
                pyglet.shapes.Line(x1, y1, x2, y2, thickness=3, color=(0, 200, 0)).draw()
                
        # Draw denormalized template if available
        if self.denorm_template is not None and len(self.denorm_template) > 1:
            for i in range(len(self.denorm_template) - 1):
                x1, y1 = self.denorm_template[i]
                x2, y2 = self.denorm_template[i + 1]
                pyglet.shapes.Line(x1, y1, x2, y2, thickness=3, color=(255, 0, 0)).draw()
                
        self.label.draw()
        self.save_ui.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        # Delegate UI click handling to GestureUI
        handled = self.save_ui.handle_mouse_press(x, y, button, self.save_ui.speed_button_width, self.save_stroke)
        if handled:
            return

        self.stroke_points = [(x, y)]
        self.stroke_times = [int(time.time() * 1000)]
        self.label.text = "Drawing..."
        self.denorm_template = None
        self.last_stroke_points = []
        self.last_stroke_times = []
        self._mouse_buttons = set([button])
        self._mouse_x, self._mouse_y = x, y

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        # Only allow drawing if not interacting with input or save button
        if not self.gesture_saver.input_active and not (200 <= x <= 280 and 10 <= y <= 42):
            if buttons & mouse.LEFT:
                import time
                self.stroke_points.append((x, y))
                self.stroke_times.append(int(time.time() * 1000))
                self._mouse_x, self._mouse_y = x, y

    def on_text(self, text):
        self.save_ui.handle_text(text)

    def on_key_press(self, symbol, modifiers):
        self.save_ui.handle_key_press(symbol)

    def save_stroke(self):
        # Save the current stroke if drawing, otherwise save the last recognized stroke
        points_to_save = self.stroke_points if self.stroke_points else getattr(self, 'last_stroke_points', [])
        times_to_save = self.stroke_times if self.stroke_points else getattr(self, 'last_stroke_times', [])
        filename_base = self.gesture_saver.input_text.strip()
        if not filename_base:
            self.gesture_saver.save_message = 'Enter a filename.'
            return
        self.gesture_saver.save_gesture(filename_base, points_to_save, times_to_save)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        self._mouse_buttons.discard(button)

        if button != mouse.LEFT or len(self.stroke_points) <= 1:
            return
        
        # Flip Y axis for pyglet (origin is bottom-left, but most gesture datasets use top-left)
        points_np = np.array(self.stroke_points, dtype=float)
        if points_np.shape[0] > 0:
            max_y = np.max(points_np[:, 1])
            min_y = np.min(points_np[:, 1])
            points_np = points_np.copy()
            points_np[:, 1] = max_y - (points_np[:, 1] - min_y)
        pred = self.recognizer.recognize(points_np)
        label, _, denormalized, confidence = pred
        self.label.text = f"Prediction: {label} (Confidence: {confidence:.2f})"
        if denormalized is not None and len(denormalized) > 0:
            denormalized[:, 1] = max_y - (denormalized[:, 1] - min_y)
        self.denorm_template = denormalized
        self.last_stroke_points = self.stroke_points.copy()
        self.last_stroke_times = self.stroke_times.copy()
        self.stroke_points = []
        self.stroke_times = []

@click.command()
@click.option("--async-loading", "-a", is_flag=True, help="Load templates asynchronously")
def main(async_loading: bool):
    recognizer_args = {}
    recognizer = AsyncRecognizer(**recognizer_args) if async_loading else Recognizer(**recognizer_args)
    window = DrawingWindow(recognizer, width=600, height=400, caption="$1 Recognizer Demo")
    window.run()

if __name__ == "__main__":
    main()
