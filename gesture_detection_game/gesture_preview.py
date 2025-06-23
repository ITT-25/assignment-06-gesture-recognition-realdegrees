import pyglet
import numpy as np

class GesturePreview:
    """Handles drawing the gesture preview box and direction arrow."""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, template: np.ndarray = None):
        # Draw background
        sample_bg = pyglet.shapes.Rectangle(self.x, self.y, self.width, self.height, color=(220,220,220))
        sample_bg.opacity = 220
        sample_bg.draw()
        if template is None or len(template) <= 1:
            return
        # Flip X for preview
        t = template.copy()
        min_x, min_y = np.min(t, axis=0)
        max_x, max_y = np.max(t, axis=0)
        t[:, 0] = max_x - (t[:, 0] - min_x)
        size = max(np.max(t, axis=0) - np.min(t, axis=0))
        if size == 0:
            size = 1
        scale = 0.8 * min(self.width, self.height) / size
        t_norm = (t - np.min(t, axis=0)) * scale
        offset_x = self.x + self.width/2 - np.mean(t_norm[:,0])
        offset_y = self.y + self.height/2 - np.mean(t_norm[:,1])
        t_disp = t_norm + np.array([offset_x, offset_y])
        for i in range(len(t_disp)-1):
            x1, y1 = t_disp[i]
            x2, y2 = t_disp[i+1]
            pyglet.shapes.Line(x1, y1, x2, y2, thickness=3, color=(100, 0, 200)).draw()
        # Draw direction arrow fromfirst point to centroid of first 4 points sticking out backwards
        n = min(4, len(t_disp))
        x0, y0 = t_disp[0]
        if n > 1:
            centroid = np.mean(t_disp[:n], axis=0)
            dx, dy = centroid[0] - x0, centroid[1] - y0
            arrow_length = 0
            for i in range(n-1):
                arrow_length += np.hypot(t_disp[i+1][0] - t_disp[i][0], t_disp[i+1][1] - t_disp[i][1])
            arrow_length *= 2
            length = np.hypot(dx, dy)
            if length > 0 and arrow_length > 0:
                ux, uy = dx / length, dy / length
                tip_x = x0
                tip_y = y0
                base_x = tip_x - ux * arrow_length
                base_y = tip_y - uy * arrow_length
                perp_x = -uy
                perp_y = ux
                arrow_width = 10
                left_x = tip_x - ux * 10 + perp_x * arrow_width
                left_y = tip_y - uy * 10 + perp_y * arrow_width
                right_x = tip_x - ux * 10 - perp_x * arrow_width
                right_y = tip_y - uy * 10 - perp_y * arrow_width
                pyglet.shapes.Line(base_x, base_y, tip_x, tip_y, thickness=3, color=(255, 80, 0)).draw()
                pyglet.shapes.Line(tip_x, tip_y, left_x, left_y, thickness=3, color=(255, 80, 0)).draw()
                pyglet.shapes.Line(tip_x, tip_y, right_x, right_y, thickness=3, color=(255, 80, 0)).draw()
        # Draw label
        label_text = "Gesture starts at the red arrow"
        label_x = self.x + self.width / 2
        label_y = self.y - 8
        pyglet.text.Label(
            label_text,
            font_size=12,
            x=label_x,
            y=label_y,
            anchor_x='center',
            anchor_y='top',
            color=(80, 0, 0, 255)
        ).draw()
