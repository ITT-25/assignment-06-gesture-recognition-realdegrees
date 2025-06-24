[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/HqZjtAXJ)

# Setup

1. Clone the repo
2. `cd` into the **root** directory
3. Setup and activate a virtual env **(Python 3.12)**
4. `pip install -r requirements.txt`
5. Download the `Unistroke gesture logs: XML` from [Wobbrock's Website](https://depts.washington.edu/acelab/proj/dollar/index.html)
6. Move the dataset into the `datasets/xml_logs` directory

> ⚠️ Due to some import shenanigans you **must** run all applications as modules `-m` **from the root directory**

> ⚠️ The `requirements.txt` includes `jupyter` and `ipykernel` so you can use it for Task 1,2 and 4 but also as a kernel for Task 3

# 1. $1 Gesture Recognizer

> ⚠️ For all non-notebook tasks the templates for recognizer are loaded in the background.  
The window will open relatively fast but might stutter slightly while data is still loaded. Check console output for loading progress.  

This program is a python implementation of the [1$ Unistroke Recognizer](https://depts.washington.edu/acelab/proj/dollar/index.html).  
It was modeled based on [this pseudo-code](https://depts.washington.edu/acelab/proj/dollar/dollar.pdf).  
The `Recognizer` class loads the gesture templates on initialization and provides a `recognize` method to label a path array.  
It can be tested via a GUI using the instructions below.  

```sh
python -m recognizer.pyglet_gui -a
```

Draw any of the shapes present in the template shapes by pressing and holding `Left Click`.  
Once you let go of `Left Click` the closest matching shape will be overlayed where you drew your shape with a label and confidence value at the top.  
<div align="left">
    <img src="docs/unistrokes.gif" alt="Unistroke gesture templates" width="170px" />
</div>

# 2. Mid-Air Gestures with $1 Recognizer

This program gives you the ability to move your pointer and press mouse buttons.  
When it opens it automatically launches the GUI from Task 1 (Can be minimized if not needed).  

```sh
# Debug flag is optional
python -m pointing_input.pointing_input --video-id 0 -d
```
## 2.2 Control Instructions

The application is controlled using simple gestures.   
The controls work best with an open palm facing towards the camera.  
(Both this task and task 4 are hardcoded to use the right hand for gesture recognition)  

- `Connecting` **index** finger and **thumb** will trigger `Left Mouse Button Down`  
- `Releasing` **index** finger and **thumb** will trigger `Left Mouse Button Up`  
- `Holding` **index** finger and **thumb** will move the mouse 
- `Extending` **index** finger will move the mouse

> ⚠️ The inputs are actively smoothed slightly to allow precise movement at the cost of a minimal delay
The delay is noticeable but better than jittery input

## 2.3 Saving Templates

To create your own dataset you can save gestures using the GUI.  
1. Enter the name for the gesture template in text input field at the top (next to the add button)  
2. Draw your gesture
3. Press the `Add` button to store the template in memory (A list of all created templates is shown in the bottom right)  
(You can also use `Auto Add` to automatically save every drawn gesture under the given name for bulk recording)
4. *Repeat steps 1-3 for as many gestures as you want to save*
5. Enter a `Subject ID` *(numeric only)* in the text input field at the bottom
6. Select the `Speed` that you want to use for the recorded gesture(s) [`Slow`, `Medium`, `Fast`]
7. Press the `Save` button. Your templates will be saved in the `datasets/custom/` (path is built from subject id, speed and gesture name)
8. Press the `Clear` button to clear the list of templates in memory to record for a new subject


# 3. Comparing Gesture Recognizers

> Test Datasets: The datasets are located in the [datasets/xml_logs](datasets/xml_logs) and [datasets/custom](datasets/custom) directories.  
When the the notebook loads them it selects an equal number of samples from each dataset and loads them in the same way.

Documentation on this task is in the notebook.  

# 4. Gesture Detection Game

Due to time constraints I decided on a very rudimentary game that simply gives you a list of 10 random gestures to draw in sequence.  
To add a little pressure there is a timer that tracks how long it took you to complete the 10 gestures and how many you got right.  
To start the game press `SPACE`. A gesture will be shown in the top right corner that you will have to copy on the screen. An indicator shows the origin of the gesture.  
You have one attempt per gesture, as soon as `Left Mouse Button Up` is detected, the gesture is recognized and you will move to the next one.  
You can draw gestures with your mouse only, the pointing input program from Task 2 runs in the background so you can use it to control the mouse with your hand.  
A preview of your webcam feed is also shown for easier mid-air input coordination.  

To launch the game run the following command:

```sh
python -m gesture_detection_game.gesture_application --video-id 0 -d
```
You can adjust the width `-w` and height `-h` of the window (and your webcam) but it is recommended to stay on the default resolution for lower end devices.  