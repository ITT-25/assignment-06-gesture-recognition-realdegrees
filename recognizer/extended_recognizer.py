from typing import Tuple
import numpy as np
from recognizer import Recognizer

class ExtendedRecognizer(Recognizer):
    """Recognizer with normalization parameter tracking and denormalization capability."""

    def _normalize_with_params(self, points: np.ndarray) -> Tuple[np.ndarray, dict]:
        """Normalize input points and return normalization parameters for denormalization."""
        # 1. Resample
        resampled = self._resample(points)
        # 2. Rotation
        center_before_rot = self._centroid(resampled)
        angle = np.arctan2(resampled[0, 1] - center_before_rot[1], resampled[0, 0] - center_before_rot[0])
        rotated = self._rotate(resampled, -angle)
        # 3. Scaling
        min_vals = np.min(rotated, axis=0)
        max_vals = np.max(rotated, axis=0)
        scale = 250.0 / np.max(max_vals - min_vals)
        scaled = rotated * scale
        # 4. Translation
        center = self._centroid(scaled)
        translated = scaled - center
        params = {
            'angle': angle,
            'scale': scale,
            'center': center
        }
        return translated, params

    def _denormalize(self, points: np.ndarray, params: dict) -> np.ndarray:
        """Denormalize a stroke using normalization parameters from a reference stroke."""
        denorm = points + params['center']
        denorm = denorm / params['scale']
        denorm = self._rotate(denorm, params['angle'])
        return denorm

    def recognize(self, points: np.ndarray):
        """Recognize the input gesture and return the label, normalized template, and denormalized template."""
        normalized_points, params = self._normalize_with_params(points)
        best_label, best_template = super().recognize(normalized_points, normalize=False)
        denormalized_template = self._denormalize(best_template, params)
        return best_label, normalized_points, denormalized_template
