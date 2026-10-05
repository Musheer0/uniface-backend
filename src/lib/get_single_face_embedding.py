from uniface.detection import RetinaFace
from uniface.recognition import ArcFace
import cv2

from src.lib.get_detector import get_detector
def create_face_embedding(face_img_path:str, detector:RetinaFace):
    face_image= cv2.imread(face_img_path)
    if face_image is None:
        print(face_image)
        raise ValueError("Error reading image")
    face = detector.detect(face_image)
    if not face:
        raise ValueError("No Face Found")
    recognizer = ArcFace()
    return recognizer.get_normalized_embedding(face_image,face[0].landmarks)
    
def get_single_face_embedding(faceId:str):
    #TODO load face from vector storage
    face_vector = False
    if face_vector:
        pass
    else:
        #create embedding
        # TODO download face
        face_path = "/home/muchi/Projects/blurfield/backend/b.webp"
        detector = get_detector()
        embeddings = create_face_embedding(face_path, detector)
        #TODO upload embeddings
        return embeddings