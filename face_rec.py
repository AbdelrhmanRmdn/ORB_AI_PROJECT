from config import TEST_MODE, FACE_RECOGNITION_ENABLED, AUTHORIZED_USERS


def identify_user():
    if not FACE_RECOGNITION_ENABLED:
        print("[FACE] Face recognition disabled")
        return None

    if TEST_MODE:
        print("[FACE] Test mode active - returning demo user")
        return AUTHORIZED_USERS[0]

    try:
        import cv2
        import face_recognition

        video_capture = cv2.VideoCapture(0)

        if not video_capture.isOpened():
            print("[FACE] Could not open camera")
            return None

        ret, frame = video_capture.read()
        video_capture.release()

        if not ret:
            print("[FACE] Could not read frame from camera")
            return None

        rgb_frame = frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if face_encodings:
            print("[FACE] Face detected")
            return "Authorized User"

        print("[FACE] No face detected")
        return None

    except Exception as e:
        print(f"[FACE] Recognition error: {e}")
        return None


if __name__ == "__main__":
    print("Testing face_rec.py")

    user = identify_user()

    print(f"Detected user: {user}")
