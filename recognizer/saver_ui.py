from typing import Callable, TYPE_CHECKING, List
import pyglet
from pyglet.window import mouse
from recognizer.text_input import TextInput

if TYPE_CHECKING:
    from recognizer.gesture_saver import GestureSaver
    from recognizer.recognizer import Recognizer
    from recognizer.pyglet_gui import DrawingWindow


class GestureSaverUI:
    def __init__(
        self,
        gesture_saver: "GestureSaver",
        recognizer: "Recognizer",
        window: "DrawingWindow",
        *,
        window_width: int = 800,
        window_height: int = 600,
        autocapture_state=False,
        add_callback: Callable[[], None] = None,
        save_callback: Callable[[], None] = None,
    ):
        self.gesture_saver = gesture_saver
        self.window = window
        self.window_width = window_width
        self.window_height = window_height
        self.recognizer = recognizer
        self.autocapture = autocapture_state
        self.add_callback = add_callback if add_callback else lambda: None
        self.save_callback = save_callback if save_callback else lambda: None

        self.input_active = False
        self.subject_active = False

        self.batch = pyglet.graphics.Batch()
        margin = 5
        spacing = 10

        self.autocapture_label = pyglet.text.Label(
            "Auto Add: Off",
            font_size=14,
            x=window_width - margin - spacing,
            y=window_height - 25,
            anchor_x="right",
            anchor_y="center",
            color=(0, 0, 0, 255),
        )
        w, h = self.autocapture_label.content_width, self.autocapture_label.content_height
        self.autocapture_button = pyglet.shapes.Rectangle(
            self.autocapture_label.x - w - margin,
            self.autocapture_label.y - h / 2 - margin,
            w + margin * 2,
            h + margin * 2,
            color=(180, 255, 180),
            batch=self.batch,
        )

        self.clear_label = pyglet.text.Label(
            "Clear",
            font_size=14,
            x=self.autocapture_button.x - margin - spacing,
            y=window_height - 25,
            anchor_x="right",
            anchor_y="center",
            color=(0, 0, 0, 255),
        )
        w, h = self.clear_label.content_width, self.clear_label.content_height
        self.clear_button = pyglet.shapes.Rectangle(
            self.clear_label.x - w - margin,
            self.clear_label.y - h / 2 - margin,
            w + margin * 2,
            h + margin * 2,
            color=(255, 100, 100),
            batch=self.batch,
        )

        self.add_label = pyglet.text.Label(
            "Add",
            font_size=14,
            x=self.clear_button.x - margin - spacing,
            y=window_height - 25,
            anchor_x="right",
            anchor_y="center",
            color=(0, 0, 0, 255),
        )
        w, h = self.add_label.content_width, self.add_label.content_height
        self.add_button = pyglet.shapes.Rectangle(
            self.add_label.x - w - margin,
            self.add_label.y - h / 2 - margin,
            w + margin * 2,
            h + margin * 2,
            color=(100, 200, 255),
            batch=self.batch,
        )

        self.gesture_name_input = TextInput(
            window=self.window,
            x=self.add_button.x - margin - spacing,
            y=window_height - 25,
            align="right",
            font_size=14,
            title="Gesture Name",
        )
        self.subject_input = TextInput(
            window=self.window,
            x=15,
            y=25,
            align="left",
            font_size=14,
            only_numerical=True,
            title="Subject ID",
        )

        self.save_label = pyglet.text.Label(
            "Save",
            font_size=14,
            x=self.subject_input.input_box.x + self.subject_input.input_box.width + spacing + 20,
            y=self.subject_input.input_box.y + self.subject_input.input_box.height / 2,
            anchor_x="left",
            anchor_y="center",
            color=(0, 0, 0, 255),
        )
        w, h = self.save_label.content_width, self.save_label.content_height
        self.save_button = pyglet.shapes.Rectangle(
            self.save_label.x - margin,
            self.save_label.y - h / 2 - margin,
            w + margin * 2,
            h + margin * 2,
            color=(100, 255, 100),
            batch=self.batch,
        )

        self.custom_templates_labels: List[pyglet.text.Label] = []
        self._last_save_message = ""
        self._save_message_time = 0
        self._save_message_alpha = 255

    def draw(self):
        self.batch.draw()
        self.gesture_name_input.draw()

        self.subject_input.draw()
        self.save_button.draw()
        self.save_label.draw()

        self.add_label.draw()
        self.clear_label.draw()
        self.autocapture_button.color = (180, 255, 180) if self.autocapture else (255, 180, 180)
        self.autocapture_label.text = "Auto Add: On" if self.autocapture else "Auto Add: Off"
        self.autocapture_label.draw()

        # Draw custom templates label(s) at bottom right, stacking up
        label_counts = {}
        for label, _, _, _ in self.recognizer.custom_templates:
            label_counts[label] = label_counts.get(label, 0) + 1
        self.custom_templates_labels.clear()
        base_y = 10
        line_height = 16
        if label_counts:
            lbl = pyglet.text.Label(
                "Custom Templates",
                font_size=12,
                x=self.window_width - 10,
                y=base_y,
                anchor_x="right",
                anchor_y="bottom",
                color=(80, 80, 80, 255),
            )
            self.custom_templates_labels.append(lbl)
            lines = [f"{lbl}: {cnt}" for lbl, cnt in sorted(label_counts.items())]
            for i, line in enumerate(reversed(lines)):
                y = base_y + line_height * (i + 1)
                lbl = pyglet.text.Label(
                    line,
                    font_size=12,
                    x=self.window_width - 10,
                    y=y,
                    anchor_x="right",
                    anchor_y="bottom",
                    color=(0, 0, 0, 255),
                )
                self.custom_templates_labels.append(lbl)
        else:
            lbl = pyglet.text.Label(
                "No custom templates",
                font_size=12,
                x=self.window_width - 10,
                y=base_y,
                anchor_x="right",
                anchor_y="bottom",
                color=(120, 120, 120, 255),
            )
            self.custom_templates_labels.append(lbl)
        for lbl in self.custom_templates_labels:
            lbl.draw()

    def handle_mouse_press(
        self, x: int, y: int, button: int, save_callback: Callable[[str], None]
    ) -> bool:
        def is_pressed(rect: pyglet.shapes.Rectangle, x: int, y: int) -> bool:
            return rect.x <= x <= rect.x + rect.width and rect.y <= y <= rect.y + rect.height

        if button == mouse.LEFT:
            # Add button
            if is_pressed(self.add_button, x, y):
                self.add_callback()
                return True
            # Clear button
            if is_pressed(self.clear_button, x, y):
                self._clear_custom_templates()
                return True
            # Autocapture button
            if is_pressed(self.autocapture_button, x, y):
                self.autocapture = not self.autocapture
                return True
            # Save button
            if is_pressed(self.save_button, x, y):
                subject = self.subject_input.get_text().strip()
                if subject != "":
                    save_callback(subject)
                else:
                    print("Subject ID cannot be empty.")
                return True
            return is_pressed(self.gesture_name_input.input_box, x, y) or is_pressed(
                self.subject_input.input_box, x, y
            )
        return False

    def get_gesture_name_input(self) -> str:
        text = self.gesture_name_input.get_text().strip()
        if text == "<Gesture Name>":
            return ""
        return text

    def get_subject_input(self) -> str:
        text = self.subject_input.get_text().strip()
        if text == "<Subject ID>":
            return ""
        return text

    def _clear_custom_templates(self):
        self.recognizer.clear_custom_templates()
