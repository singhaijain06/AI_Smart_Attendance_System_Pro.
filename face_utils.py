"""
face_utils.py
Core face-processing logic used by the Flask web app so everything
(registration, training, recognition) works through the browser —
no separate desktop scripts / webcam windows needed.

The browser captures frames using its own camera (getUserMedia) and
sends them to the server as base64 JPEG images. This module decodes
them, detects faces with OpenCV's Haar Cascade, and either saves them
(registration), trains the LBPH model, or recognizes a face
(attendance).
"""

import cv2
import numpy as np
import base64
import os

DATASET_DIR = "dataset"
TRAINER_DIR = "trainer"
TRAINER_FILE = os.path.join(TRAINER_DIR, "trainer.yml")
CONFIDENCE_THRESHOLD = 70  # lower = stricter match (LBPH distance)

_face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def _decode_base64_image(data_url):
    """Converts a 'data:image/jpeg;base64,....' string into an OpenCV BGR image."""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    img_bytes = base64.b64decode(data_url)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return frame


def detect_largest_face(frame):
    """Returns the grayscale crop of the largest detected face, or None."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _face_detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
    if len(faces) == 0:
        return None
    # pick the largest face box (in case of multiple faces in frame)
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return gray[y:y + h, x:x + w]


def save_face_sample(data_url, student_id, roll_no, sample_index):
    """Decodes a browser-captured frame, detects the face, and saves it to disk.
    Returns True if a face was found and saved, False otherwise."""
    frame = _decode_base64_image(data_url)
    if frame is None:
        return False

    face_crop = detect_largest_face(frame)
    if face_crop is None:
        return False

    student_folder = os.path.join(DATASET_DIR, f"{student_id}_{roll_no}")
    os.makedirs(student_folder, exist_ok=True)
    file_path = os.path.join(student_folder, f"{sample_index}.jpg")
    cv2.imwrite(file_path, face_crop)
    return True


def train_model():
    """Trains the LBPH recognizer on everything currently in dataset/.
    Returns (success: bool, message: str)."""
    os.makedirs(TRAINER_DIR, exist_ok=True)

    if not os.path.exists(DATASET_DIR) or not os.listdir(DATASET_DIR):
        return False, "No face data found. Register at least one student first."

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    face_samples = []
    ids = []

    for folder_name in os.listdir(DATASET_DIR):
        folder_path = os.path.join(DATASET_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue
        try:
            student_id = int(folder_name.split("_")[0])
        except ValueError:
            continue

        for img_name in os.listdir(folder_path):
            img_path = os.path.join(folder_path, img_name)
            gray_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if gray_img is None:
                continue
            face_samples.append(np.array(gray_img, "uint8"))
            ids.append(student_id)

    if not face_samples:
        return False, "No valid face images found in dataset."

    recognizer.train(face_samples, np.array(ids))
    recognizer.write(TRAINER_FILE)
    return True, f"Model trained on {len(face_samples)} images for {len(set(ids))} student(s)."


def recognize_face(data_url):
    """Recognizes a face from a browser-captured frame.
    Returns (student_id, confidence) if a confident match is found, else (None, None)."""
    if not os.path.exists(TRAINER_FILE):
        return None, None

    frame = _decode_base64_image(data_url)
    if frame is None:
        return None, None

    face_crop = detect_largest_face(frame)
    if face_crop is None:
        return None, None

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(TRAINER_FILE)

    student_id, distance = recognizer.predict(face_crop)
    if distance < CONFIDENCE_THRESHOLD:
        return student_id, distance
    return None, None
