from typing import Callable, TYPE_CHECKING
import pyglet
from pyglet.window import mouse

if TYPE_CHECKING:
    from recognizer.gesture_saver import GestureSaver


class GestureSaverUI:
    def __init__(self, gesture_saver: "GestureSaver"):
        self.gesture_saver = gesture_saver
        self.input_box = pyglet.shapes.Rectangle(10, 10, 180, 32, color=(220,220,220))
        self.subject_box = pyglet.shapes.Rectangle(10, 52, 180, 32, color=(220,220,220))
        self.speed_box = pyglet.shapes.Rectangle(10, 94, 360, 32, color=(220,220,220))
        self.save_button = pyglet.shapes.Rectangle(200, 10, 80, 32, color=(180,220,180))
        self.save_label = pyglet.text.Label(self.gesture_saver.save_label_text, font_size=16, x=240, y=26, anchor_x='center', anchor_y='center', color=(0,0,0,255))
        self.input_label = pyglet.text.Label('', font_size=16, x=15, y=26, anchor_x='left', anchor_y='center', color=(0,0,0,255))
        self.subject_label = pyglet.text.Label('', font_size=16, x=15, y=68, anchor_x='left', anchor_y='center', color=(0,0,0,255))
        self.save_message_label = pyglet.text.Label('', font_size=12, x=10, y=170, anchor_x='left', anchor_y='bottom', color=(0,100,0,255))
        self.speed_button_width = 120
        self.speed_labels = [
            pyglet.text.Label(opt.capitalize(), font_size=16, x=10 + self.speed_button_width//2 + i*self.speed_button_width, y=110, anchor_x='center', anchor_y='center', color=(0,0,0,255))
            for i, opt in enumerate(self.gesture_saver.speed_options)
        ]

    def draw(self):
        self.input_box.draw()
        self.save_button.draw()
        self.save_label.text = self.gesture_saver.save_label_text
        self.save_label.draw()
        self.subject_box.draw()
        self.speed_box.draw()
        for i, label in enumerate(self.speed_labels):
            x0 = 10 + i*self.speed_button_width
            color = (180,220,180) if i == self.gesture_saver.selected_speed else (220,220,220)
            pyglet.shapes.Rectangle(x0, 94, self.speed_button_width, 32, color=color).draw()
            label.draw()
        self.input_label.text = self.gesture_saver.input_text if self.gesture_saver.input_active or self.gesture_saver.input_text else 'Enter filename...'
        self.input_label.color = (0,0,0,255) if self.gesture_saver.input_active or self.gesture_saver.input_text else (120,120,120,255)
        self.input_label.draw()
        self.subject_label.text = self.gesture_saver.subject_text if self.gesture_saver.subject_active or self.gesture_saver.subject_text else 'Enter subject...'
        self.subject_label.color = (0,0,0,255) if self.gesture_saver.subject_active or self.gesture_saver.subject_text else (120,120,120,255)
        self.subject_label.draw()
        if self.gesture_saver.save_message:
            self.save_message_label.text = self.gesture_saver.save_message
            self.save_message_label.draw()

    def handle_mouse_press(self, x: int, y: int, button: int, speed_button_width: int, save_stroke_callback: Callable[[], None]):
        if button == mouse.LEFT:
            for i in range(3):
                x0 = 10 + i*speed_button_width
                if x0 <= x <= x0 + speed_button_width and 94 <= y <= 126:
                    self.gesture_saver.selected_speed = i
                    return True
            if 10 <= x <= 190 and 52 <= y <= 84:
                self.gesture_saver.subject_active = True
                self.gesture_saver.input_active = False
                return True
            if 10 <= x <= 190 and 10 <= y <= 42:
                self.gesture_saver.input_active = True
                self.gesture_saver.subject_active = False
                return True
            else:
                self.gesture_saver.input_active = False
                self.gesture_saver.subject_active = False
            if 200 <= x <= 280 and 10 <= y <= 42:
                save_stroke_callback()
                return True
        return False

    def handle_text(self, text: str):
        if self.gesture_saver.input_active:
            if text == '\r' or text == '\n':
                self.gesture_saver.input_active = False
            elif text == '\b':
                self.gesture_saver.input_text = self.gesture_saver.input_text[:-1]
            elif len(text) == 1 and len(self.gesture_saver.input_text) < 32:
                self.gesture_saver.input_text += text
        elif self.gesture_saver.subject_active:
            if text == '\r' or text == '\n':
                self.gesture_saver.subject_active = False
            elif text == '\b':
                self.gesture_saver.subject_text = self.gesture_saver.subject_text[:-1]
            elif text.isdigit() and (len(self.gesture_saver.subject_text) > 0 or text != '0') and len(self.gesture_saver.subject_text) < 5:
                self.gesture_saver.subject_text += text

    def handle_key_press(self, symbol: int):
        if self.gesture_saver.input_active and symbol == pyglet.window.key.BACKSPACE:
            self.gesture_saver.input_text = self.gesture_saver.input_text[:-1]
        elif self.gesture_saver.subject_active and symbol == pyglet.window.key.BACKSPACE:
            self.gesture_saver.subject_text = self.gesture_saver.subject_text[:-1]
