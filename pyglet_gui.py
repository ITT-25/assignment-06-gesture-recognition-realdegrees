from typing import List, Tuple
import pyglet
from pyglet.window import mouse
import numpy as np
from recognizer import Recognizer

class DrawingWindow(pyglet.window.Window):
    def __init__(self, recognizer: Recognizer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recognizer = recognizer
        self.stroke_points: List[Tuple[float, float]] = []
        self.label = pyglet.text.Label("Draw a gesture", font_size=24, x=10, y=self.height-40, anchor_x='left', anchor_y='top', color=(0,0,0,255))
        self.set_mouse_visible(True)
        pyglet.gl.glClearColor(1, 1, 1, 1)

    def on_draw(self):
        self.clear()
        # Draw current stroke as simple lines between points
        if len(self.stroke_points) > 1:
            for i in range(len(self.stroke_points) - 1):
                x1, y1 = self.stroke_points[i]
                x2, y2 = self.stroke_points[i + 1]
                pyglet.shapes.Line(x1, y1, x2, y2, thickness=2, color=(0, 0, 0)).draw()
                
        self.label.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.stroke_points = [(x, y)]
            self.label.text = "Drawing..."

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & mouse.LEFT:
            self.stroke_points.append((x, y))

    def on_mouse_release(self, x, y, button, modifiers):
        if button == mouse.LEFT and len(self.stroke_points) > 1:
            # Flip Y axis for pyglet (origin is bottom-left, but most gesture datasets use top-left)
            points_np = np.array(self.stroke_points, dtype=float)
            if points_np.shape[0] > 0:
                max_y = np.max(points_np[:, 1])
                min_y = np.min(points_np[:, 1])
                points_np = points_np.copy()
                points_np[:, 1] = max_y - (points_np[:, 1] - min_y)
            pred = self.recognizer.recognize(points_np)
            self.label.text = f"Prediction: {pred}"
            self.stroke_points = []

if __name__ == "__main__":
    recognizer = Recognizer()
    window = DrawingWindow(recognizer, width=600, height=400, caption="$1 Recognizer Demo")
    pyglet.app.run()
