[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/HqZjtAXJ)

# Setup

1. Clone the repo
2. `cd` into the **root** directory
3. Setup and activate a virtual env **(Python 3.12)**
4. `pip install -r requirements.txt`
5. Download the `Unistroke gesture logs: XML` from [Wobbrock's Website](https://depts.washington.edu/acelab/proj/dollar/index.html)
6. Move the dataset into the `datasets/xml_logs` directory

# 1$ Gesture Recognizer

This program is a python implementation of the [1$ Unistroke Recognizer](https://depts.washington.edu/acelab/proj/dollar/index.html).  
It was modeled based on [this pseudo-code](https://depts.washington.edu/acelab/proj/dollar/dollar.pdf).  
The `Recognizer` class loads the gesture templates on initialization and provides a `recognize` method to label a path array.  
It can be tested via a GUI using the instructions below.  

```sh
cd .\recognizer
python .\pyglet_gui.py --template-path ../datasets/xml_logs -a
```

Draw any of the shapes present in the template shapes by pressing and holding `Left Click`.  
Once you let go of `Left Click` the closest matching shape will be overlayed where you drew your shape with a label and confidence value at the top.  
<div align="left">
    <img src="docs/unistrokes.gif" alt="Unistroke gesture templates" width="170px" />
</div>
