import pyglet
import cv2
import click
from recognizer.recognizer import AsyncRecognizer
from pointing_input.hand_detector import HandDetector
from pointing_input.mouse_mapper import MouseMapper
from gesture_detection_game.gesture_window import GestureGameWindow

@click.command()
@click.option("--video-id", "-c", default=0, help="ID of the webcam you want to use", type=int, show_default=True)
@click.option("--cam-width", "-w", default=640, help="Width of the webcam frame", type=int, show_default=True)
@click.option("--cam-height", "-h", default=480, help="Height of the webcam frame", type=int, show_default=True)
@click.option("--debug", "-d", is_flag=True, help="Enable debug mode")
@click.option("--rounds", "-r", default=10, help="Number of rounds to play", type=int, show_default=True)
def cli(video_id: int, cam_width: int, cam_height: int, debug: bool, rounds: int):
    print(f"Starting webcam capture with camera ID: {video_id}")
    cap = cv2.VideoCapture(video_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)
    if not cap.isOpened():
        print(f"Error: Could not open camera with ID {video_id}")
        return
    recognizer = AsyncRecognizer()

    window = GestureGameWindow(recognizer=recognizer, width=cam_width, height=cam_height, caption="Gesture Tracing Game")
    window.app.max_rounds = rounds
    hand_detector = HandDetector()
    mouse = MouseMapper(window.width, window.height)
    def capture_loop(dt: float) -> None:
        try:
            ret, frame = cap.read()
            if not ret:
                return
            else:
                frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            right, left = hand_detector.detect_landmarks(frame)
            mouse.process(left, right, use_right=True)
            if debug:
                if left:
                    for i, landmark in enumerate(left.landmarks):
                        x = int(landmark[0] * w)
                        y = int(landmark[1] * h)
                        cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
                        if i == 0:
                            cv2.putText(frame, left.gesture, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                if right:
                    for i, landmark in enumerate(right.landmarks):
                        x = int(landmark[0] * w)
                        y = int(landmark[1] * h)
                        cv2.circle(frame, (x, y), 1, (255, 0, 0), -1)
                        if i == 0:
                            cv2.putText(frame, right.gesture, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            window.update_background(frame)
        except Exception as e:
            print(f"Exception in capture_loop: {e}")
            
    pyglet.clock.schedule_interval(capture_loop, 1/60)
    pyglet.app.run()
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    cli()
