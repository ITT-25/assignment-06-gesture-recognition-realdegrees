import pyglet
from pyglet.window import mouse
from typing import TYPE_CHECKING, Literal
import pyglet.window.key

if TYPE_CHECKING:
    from recognizer.pyglet_gui import DrawingWindow

class TextInput:
    def __init__(self, window: "DrawingWindow", x: int, y: int, align: Literal['left', 'center', 'right'], font_size: int = 14, only_numerical: bool = False, title: str = None):
        self.window = window
        self.input_label = pyglet.text.Label(" " * 30, font_size=font_size, x=x, y=y, anchor_x=align, anchor_y='center', color=(0,0,0,255))
        self.only_numerical = only_numerical
        w, h = self.input_label.content_width, self.input_label.content_height
        self.input_box = pyglet.shapes.Rectangle(
            x - w * (-1 if align == 'left' else 1) - 5,  # margin
            y - h/2 - 5,
            w + 10,
            h + 10,
            color=(220,220,220)
        )
        self.input_active = False
        self.title_label = pyglet.text.Label(
            title,
            font_size=8,
            x=self.input_box.x + 2,
            y=self.input_box.y + self.input_box.height + 5,
            anchor_x='left',
            anchor_y='top',
            color=(0,0,0,255)
        ) if title else None
       
        # Register event handlers
        window.push_handlers(self)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int = None):
        if button == mouse.LEFT:
            if (self.input_box.x <= x <= self.input_box.x + self.input_box.width and
                self.input_box.y <= y <= self.input_box.y + self.input_box.height):
                self.input_active = True
            else:
                self.input_active = False
        return False

    def on_text(self, text: str):
        if self.input_active:
            if text == '\r' or text == '\n':
                self.input_active = False
            elif text == '\b':
                self.input_label.text = self.input_label.text[:-1]
            else:
                # Only allow digits if only_numerical is True
                if self.only_numerical and not text.isdigit():
                    return
                self.input_label.text += text

    def on_key_press(self, symbol, modifiers):
        if self.input_active and symbol == pyglet.window.key.BACKSPACE:
            self.input_label.text = self.input_label.text[:-1]
            return True
        return False

    def draw(self):
        # Draw the input box
        self.input_box.draw()
        
        # Set color based on state
        if self.input_label.text.strip() != '':
            self.input_label.color = (0,0,0,255)
        else:
            self.input_label.color = (120,120,120,255)
        self.input_label.draw()
        
        if self.title_label:
            self.title_label.draw()

    def get_text(self):
        t = self.input_label.text.strip()
        return t

    def set_text(self, text: str):
        self.input_label.text = text

    def is_active(self):
        return self.input_active
