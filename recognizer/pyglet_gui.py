from typing import List, Optional, Tuple
import pyglet
from pyglet.window import mouse
import numpy as np
from recognizer import Recognizer
from extended_recognizer import ExtendedRecognizer
import click

class DrawingWindow(pyglet.window.Window):
    def __init__(self, recognizer: Recognizer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recognizer = recognizer
        self.stroke_points: List[Tuple[float, float]] = []
        self.label = pyglet.text.Label("Draw a gesture", font_size=24, x=10, y=self.height-40, anchor_x='left', anchor_y='top', color=(0,0,0,255))
        self.set_mouse_visible(True)
        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.denorm_template = None  # Store denormalized template for drawing

    def on_draw(self):
        self.clear()
        # Draw current stroke as simple lines between points
        if len(self.stroke_points) > 1:
            for i in range(len(self.stroke_points) - 1):
                x1, y1 = self.stroke_points[i]
                x2, y2 = self.stroke_points[i + 1]
                pyglet.shapes.Line(x1, y1, x2, y2, thickness=2, color=(0, 0, 0)).draw()
        # Draw denormalized template if available
        if self.denorm_template is not None and len(self.denorm_template) > 1:
            for i in range(len(self.denorm_template) - 1):
                x1, y1 = self.denorm_template[i]
                x2, y2 = self.denorm_template[i + 1]
                pyglet.shapes.Line(x1, y1, x2, y2, thickness=2, color=(255, 0, 0)).draw()
        self.label.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.stroke_points = [(x, y)]
            self.label.text = "Drawing..."
            self.denorm_template = None  # Clear template overlay on new stroke

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
            if isinstance(self.recognizer, ExtendedRecognizer):
                label, _, denorm_template = pred
                self.label.text = f"Prediction: {label}"
                # Flip Y axis back for drawing
                if denorm_template is not None and len(denorm_template) > 0:
                    denorm_template = denorm_template.copy()
                    denorm_template[:, 1] = max_y - (denorm_template[:, 1] - min_y)
                self.denorm_template = denorm_template
            else:
                self.label.text = f"Prediction: {pred}"
                self.denorm_template = None
            self.stroke_points = []

@click.command()
@click.option("--template-path", "-p", type=click.Path(exists=True), help="Path to gesture template XML files")
@click.option("--extended", "-e", is_flag=True, help="Use ExtendedRecognizer with denormalized template overlay")
def main(template_path: Optional[str], extended: bool):
    if extended:
        recognizer = ExtendedRecognizer(template_path=template_path) if template_path else ExtendedRecognizer()
    else:
        recognizer = Recognizer(template_path=template_path) if template_path else Recognizer()
    DrawingWindow(recognizer, width=600, height=400, caption="$1 Recognizer Demo")
    pyglet.app.run()

if __name__ == "__main__":
    main()
