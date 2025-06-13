[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/HqZjtAXJ)

# Setup

1. Clone the repo
2. `cd` into the **root** directory
3. Setup and activate a virtual env **(Python 3.12)**
4. `pip install -r requirements.txt`

TODO add dataset download instructions

# 1$ Gesture Recognizer

This program is a python implementation of the [1$ Unistroke Recognizer](https://depts.washington.edu/acelab/proj/dollar/index.html).  
It was modeled based on [this pseudo-code](https://depts.washington.edu/acelab/proj/dollar/dollar.pdf).  
The `Recognizer` class loads the gesture templates on initialization and provides a `recognize` method to label a path array.  
It can be tested via a [GUI](./recognizer/pyglet_gui.py) using the instructions below.  

```sh
cd .\recognizer
python .\pyglet_gui.py --template-path ../datasets/xml_logs # Use the extended recognizer below for a better GUI
```

## Extended 1$ Recognizer

For a better visualization I added an `ExtendedRecognizer` (hoping that it might be useful for later tasks too).  
This class overrides the `recognize` method to store normalization params and then apply the inverse of the normalization to the best matching template.  
This puts the matching template in the exact same coordinate space, rotation and position as the input stroke.  
Basically it can be used to perfectly overlay the template that had the best match.  
Use the `--extended` flag to replace the default `Recognizer` with the `ExtendedRecognizer` to add an overlay after stroke detection to the GUI.  

```sh
python .\pyglet_gui.py --template-path ../datasets/xml_logs --extended
```