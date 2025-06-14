import cv2
import click
from pointing_input import HandDetector, MouseMapper
from recognizer import DrawingWindow, AsyncRecognizer

hand_detector = HandDetector()
recognizer = AsyncRecognizer()
window = DrawingWindow(recognizer=recognizer)
mouse = MouseMapper(window.width, window.height)

@click.command()
@click.option("--video-id", "-c", default=0, help="ID of the webcam you want to use", type=int, show_default=True)
@click.option("--cam-width", "-w", default=640, help="Width of the webcam frame", type=int, show_default=True)
@click.option("--cam-height", "-h", default=480, help="Height of the webcam frame", type=int, show_default=True)
@click.option("--debug", "-d", is_flag=True, help="Enable debug mode")
def main(video_id: int, cam_width: int, cam_height: int, debug: bool) -> None:
    print(f"Starting webcam capture with camera ID: {video_id}")
    cap = cv2.VideoCapture(video_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)

    if not cap.isOpened():
        print(f"Error: Could not open camera with ID {video_id}")
        return

    def capture_loop(dt: float) -> None:
        ret, frame = cap.read()
        if not ret:
            return
        else:
            # Flip frame
            frame = cv2.flip(frame, 1)

        h, w = frame.shape[:2]
        # Detect hand landmarks
        right, left = hand_detector.detect_landmarks(frame) # ! Left and right are swapped due to the frame flipping
        mouse.process(left, right, use_right=True)

        # If no hand is detected, clear the gesture queue
        if not left and not right:
            # gesture_queue.clear()
            pass

        if debug:
            # Draw landmarks on the frame
            if left:
                for i, landmark in enumerate(left.landmarks):
                    x = int(landmark[0] * w)
                    y = int(landmark[1] * h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
                    if i == 0:
                        cv2.putText(frame, left.gesture, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            if right:
                for i, landmark in enumerate(right.landmarks):
                    x = int(landmark[0] * w)
                    y = int(landmark[1] * h)
                    cv2.circle(frame, (x, y), 3, (255, 0, 0), -1)
                    if i == 0:
                        cv2.putText(frame, right.gesture, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        window.update_background(frame)

    window.run(capture_loop)
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
