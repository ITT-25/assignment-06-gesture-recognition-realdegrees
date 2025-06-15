import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Tuple

class GestureSaver:
    def __init__(self):
        self.input_text = ''
        self.input_active = False
        self.subject_text = ''
        self.subject_active = False
        self.speed_options = ['fast', 'medium', 'slow']
        self.selected_speed = 1  # default to 'medium'
        self.save_message = ''
        self.save_label_text = 'Save'

    def get_subject_folder(self):
        subject = self.subject_text.strip() or '1'
        return f"s{int(subject):02d}" if len(subject) < 3 else f"s{subject}"

    def get_speed(self):
        return self.speed_options[self.selected_speed]

    def get_save_dir(self):
        subject_folder = self.get_subject_folder()
        speed = self.get_speed()
        return os.path.join(os.path.dirname(__file__), '..', 'datasets', 'custom', subject_folder, speed)

    def get_next_filename(self, filename_base: str) -> Tuple[str, int]:
        save_dir = self.get_save_dir()
        os.makedirs(save_dir, exist_ok=True)
        existing_files = os.listdir(save_dir)
        pattern = re.compile(rf'^{re.escape(filename_base)}(\d+).xml$')
        max_num = 0
        for fname in existing_files:
            m = pattern.match(fname)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
        next_num = max_num + 1
        filename = f"{filename_base}{next_num:02d}"
        return filename, next_num

    def save_gesture(self, filename_base: str, points: List[Tuple[float, float]], times: List[int]):
        if not points or len(points) < 2:
            self.save_message = 'No stroke to save.'
            return False
        subject = self.subject_text.strip() or '1'
        speed = self.get_speed()
        save_dir = self.get_save_dir()
        filename, next_num = self.get_next_filename(filename_base)
        filepath = os.path.join(save_dir, filename + '.xml')
        now = datetime.now()
        duration = times[-1] - times[0] if len(times) > 1 else 0
        gesture_elem = ET.Element('Gesture', {
            'Name': filename,
            'Subject': subject,
            'Speed': speed,
            'Number': str(next_num),
            'NumPts': str(len(points)),
            'Millseconds': str(duration),
            'AppName': 'Gestures',
            'AppVer': '1.0',
            'Date': now.strftime('%A, %B %d, %Y'),
            'TimeOfDay': now.strftime('%I:%M:%S %p')
        })
        t0 = times[0]
        for (x, y), t in zip(points, times):
            ET.SubElement(gesture_elem, 'Point', {
                'X': str(int(x)),
                'Y': str(int(y)),
                'T': str(t - t0)
            })
        self._indent_xml(gesture_elem)
        tree = ET.ElementTree(gesture_elem)
        try:
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
            rel_path = os.path.relpath(filepath, os.path.join(os.path.dirname(__file__), '..'))
            self.save_message = f'Saved: {rel_path}'
            self.save_label_text = 'Save'
            return True
        except Exception as e:
            self.save_message = f'Error: {e}'
            self.save_label_text = 'Save'
            return False

    def _indent_xml(self, elem: ET.Element, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            for e in elem:
                self._indent_xml(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
