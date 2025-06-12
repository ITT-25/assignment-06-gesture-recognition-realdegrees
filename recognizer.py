import os
from typing import List, Tuple
import xml.etree.ElementTree as ET
import numpy as np
from sklearn.discriminant_analysis import StandardScaler
from tqdm import tqdm
from scipy.signal import resample

# TODO: add rotation normaliztion so that dataset strokes and live strokes start at the same origin within the same boundary


class Stroke:
    def __init__(self, name, points):
        self.name = name
        self.points = points

    def add_point(self, point):
        self.points.append(point)


class UnistrokeRecognizer:
    def __init__(self, num_points=64):
        self.num_points = num_points
        self.data: List[Tuple[str, np.ndarray]] = self._load_data()
        print(f'Loaded {len(self.data)} strokes from XML files.')
        print(self.data)

    def _load_data(self) -> List[Tuple[str, np.ndarray]]:
        data: List[Tuple[str, np.ndarray]] = []
        for root, subdirs, files in os.walk('xml_logs'):
            if 'ipynb_checkpoint' in root:
                continue

            if len(files) > 0:
                for f in tqdm(files):
                    if '.xml' in f:
                        fname = f.split('.')[0]
                        label = fname[:-2]

                        xml_root = ET.parse(f'{root}/{f}').getroot()

                        points = []
                        for element in xml_root.findall('Point'):
                            x = element.get('X')
                            y = element.get('Y')
                            points.append([x, y])

                        points = np.array(points, dtype=float)

                        scaler = StandardScaler()
                        points = scaler.fit_transform(points)

                        resampled = resample(points, self.num_points)

                        # TODO rotation normalization

                        data.append((label, resampled))
        return data

    def predict(self, points: np.ndarray) -> str:
        """Predict the label for the given points."""

        scaler = StandardScaler()
        points = scaler.fit_transform(points)

        # Resample to match the number of points
        resampled = resample(points, self.num_points)

        # TODO rotation normalization

        # Calculate distances to each stroke in the dataset
        distances = []
        for label, stroke in self.data:
            distance = self.get_stroke_distance_avg(resampled, stroke)
            distances.append((label, distance))

        # Sort by distance and return the label with the smallest distance
        distances.sort(key=lambda x: x[1])
        return distances[0][0]

    def get_stroke_distance_avg(self, stroke1: np.ndarray, stroke2: np.ndarray) -> float:
        """Calculate the average distance between each point in the given strokes."""
        if len(stroke1) != len(stroke2):
            raise ValueError("Strokes must have the same number of points.")

        return np.mean(np.linalg.norm(stroke1 - stroke2, axis=1))
