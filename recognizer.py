import os
import numpy as np
import xml.etree.ElementTree as ET
from typing import List, Tuple
import sys


class Recognizer:
    """Python implementation of the 1$ unistroke recognizer based on this pseudo code: https://depts.washington.edu/acelab/proj/dollar/dollar.pdf."""
    def __init__(self, *, template_path: str = "datasets/xml_logs", num_points: int = 64) -> None:
        """Load gesture templates from XML files with a loading bar."""
        self.num_points = num_points
        data: List[Tuple[str, np.ndarray]] = []
        xml_files = []
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
            normalized_points = self._normalize(points_array)
            data.append((label, normalized_points))
            # Loading bar
            bar_len = 30
            filled_len = int(bar_len * idx // total)
            bar = '=' * filled_len + '-' * (bar_len - filled_len)
            sys.stdout.write(f"\rLoading gesture templates: [{bar}] {idx}/{total}")
            sys.stdout.flush()
        print()
        self.templates = data

    def _normalize(self, points: np.ndarray) -> np.ndarray:
        """Normalize input points."""
        resampled = self._resample(points)
        rotated = self._rotate_to_zero(resampled)
        scaled = self._scale_to_square(rotated, 250.0)
        translated = self._translate_to_origin(scaled)
        return translated

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

    def _rotate_to_zero(self, points: np.ndarray) -> np.ndarray:
        """Rotate points so that the first point is at zero angle to centroid."""
        center = self._centroid(points)
        angle = np.arctan2(points[0, 1] - center[1], points[0, 0] - center[0])
        return self._rotate(points, -angle)

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

    def recognize(self, points: np.ndarray) -> str:
        """Recognize the input gesture."""
        candidate = self._normalize(points)
        best_score = float("inf")
        best_label = ""

        for label, template in self.templates:
            dist = self._path_distance(candidate, template)
            if dist < best_score:
                best_score = dist
                best_label = label

        return best_label

    def _path_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute average distance between corresponding points."""
        return np.mean(np.linalg.norm(a - b, axis=1))
