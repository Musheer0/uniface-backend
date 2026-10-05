import cv2
from uniface.detection import RetinaFace
from uniface.draw import draw_detections

detector = RetinaFace()
cap = cv2.VideoCapture(0)

print("Press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = detector.detect(frame)

    draw_detections(image=frame, faces=faces)

    cv2.imshow("UniFace - Press 'q' to quit", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()