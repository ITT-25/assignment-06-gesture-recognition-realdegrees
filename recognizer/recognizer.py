import os
import numpy as np
import xml.etree.ElementTree as ET
from typing import List, Tuple
import sys
import threading
import time

DEFAULT_TEMPLATE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../datasets/xml_logs"))
class Recognizer:
    """Python implementation of the 1$ unistroke recognizer based on this pseudo code: https://depts.washington.edu/acelab/proj/dollar/dollar.pdf."""
    def __init__(self, *, template_path: str = DEFAULT_TEMPLATE_PATH, num_points: int = 64, load_async: bool = False) -> None:
        self.num_points = num_points
        self.templates: List[Tuple[str, np.ndarray]] = []
        self.loading = True
        if load_async:
            self._loading_thread = threading.Thread(target=self._load_templates, args=(template_path,), daemon=True)
            self._loading_thread.start()
        else:
            self._load_templates(template_path)

    def _load_templates(self, template_path: str, yield_to_main: bool = True):
        xml_files = []
        if not os.path.exists(template_path):
            print(f"Warning: Template path '{template_path}' does not exist.")
        for root, _, files in os.walk(template_path):
            for file_name in files:
                if file_name.endswith(".xml"):
                    xml_files.append((root, file_name))
        total = len(xml_files)
        for idx, (root, file_name) in enumerate(xml_files, 1):
            label = file_name.split(".")[0][:-2]
            file_path = os.path.join(root, file_name)
            xml_root = ET.parse(file_path).getroot()
            points = []
            for element in xml_root.findall("Point"):
                x = float(element.get("X"))
                y = float(element.get("Y"))
                points.append([x, y])
            points_array = np.array(points, dtype=float)
            normalized_points, _ = self.normalize(points_array)
            self.templates.append((label, normalized_points))
            # Loading bar
            if idx % 5 == 0 or idx == total:
                bar_len = 30
                filled_len = int(bar_len * idx // total)
                bar = '=' * filled_len + '-' * (bar_len - filled_len)
                sys.stdout.write(f"\rLoading gesture templates: [{bar}] {idx}/{total}")
                sys.stdout.flush()
            if yield_to_main:
                time.sleep(0.001)  # Yield to main thread to reduce lag
        print()


    def normalize(self, points: np.ndarray) -> Tuple[np.ndarray, dict]:
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

    def denormalize(self, points: np.ndarray, params: dict) -> np.ndarray:
        denorm = points + params['center']
        denorm = denorm / params['scale']
        denorm = self._rotate(denorm, params['angle'])
        return denorm

    def _resample(self, points: np.ndarray) -> np.ndarray:
        """Resample points to fixed number."""
        points = points.tolist()
        distances = np.sqrt(np.sum(np.diff(points, axis=0)**2, axis=1))
        path_length = np.sum(distances)
        interval = path_length / (self.num_points - 1)

        resampled = [points[0]]
        accumulated_distance = 0.0
        i = 1
        while i < len(points):
            dist = np.linalg.norm(np.array(points[i]) - np.array(points[i - 1]))
            if (accumulated_distance + dist) >= interval:
                t = (interval - accumulated_distance) / dist
                new_point = [
                    points[i - 1][0] + t * (points[i][0] - points[i - 1][0]),
                    points[i - 1][1] + t * (points[i][1] - points[i - 1][1])
                ]
                resampled.append(new_point)
                points.insert(i, new_point)
                accumulated_distance = 0.0
                i += 1 
            else:
                accumulated_distance += dist
                i += 1

        while len(resampled) < self.num_points:
            resampled.append(points[-1])

        return np.array(resampled)

    def _rotate(self, points: np.ndarray, angle: float) -> np.ndarray:
        """Rotate points by given angle."""
        center = self._centroid(points)
        new_points = []
        cos_angle = np.cos(angle)
        sin_angle = np.sin(angle)
        for p in points:
            px, py = p
            cx, cy = center
            qx = (px - cx) * cos_angle - (py - cy) * sin_angle + cx
            qy = (px - cx) * sin_angle + (py - cy) * cos_angle + cy
            new_points.append([qx, qy])
        return np.array(new_points)

    def _scale_to_square(self, points: np.ndarray, size: float) -> np.ndarray:
        """Scale points to fit into a square."""
        min_vals = np.min(points, axis=0)
        max_vals = np.max(points, axis=0)
        scale = size / np.max(max_vals - min_vals)
        return points * scale

    def _translate_to_origin(self, points: np.ndarray) -> np.ndarray:
        """Translate points so centroid is at origin."""
        center = self._centroid(points)
        return points - center

    def _centroid(self, points: np.ndarray) -> np.ndarray:
        """Compute centroid of points."""
        return np.mean(points, axis=0)
    

    def recognize(self, points: np.ndarray):
        """Recognize the input gesture.
        Returns the label, normalized template, denormalized template, and confidence (0-1).
        """
        normalized_points, params = self.normalize(points)
        best_label, best_template, best_score = self.match(normalized_points)
        denormalized_template = self.denormalize(best_template, params)
        alpha = 0.01
        confidence = np.exp(-alpha * best_score)
        return best_label, normalized_points, denormalized_template, confidence

    # TODO: Possible enhancement but would differ from the original algorithm: sort by avg distance and return the most dominant label in the N lowest distance candidates
    def match(self, candidate: np.ndarray) -> Tuple[str, np.ndarray, float]:
        """Match the candidate gesture against the templates.
        
        Returns the label of the best matching template, the template itself, and the distance score."""
        best_score = float("inf")
        best_template: Tuple[str, np.ndarray] = ("", np.array([]))
        for label, template in self.templates:
            dist = self._path_distance(candidate, template)
            if dist < best_score:
                best_score = dist
                best_template = (label, template)
        return best_template[0], best_template[1], best_score

    def _path_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute average distance between corresponding points."""
        return np.mean(np.linalg.norm(a - b, axis=1))
