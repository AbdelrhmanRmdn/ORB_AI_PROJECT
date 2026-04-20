import time
from config import TEST_MODE, FACE_RECOGNITION_ENABLED, AUTHORIZED_USERS


def identify_user():
    if not FACE_RECOGNITION_ENABLED:
        print("[FACE] Face recognition disabled")
        return None

    if TEST_MODE:
        print("[FACE] Test mode active - returning demo user")
        return AUTHORIZED_USERS[0] if AUTHORIZED_USERS else "Demo User"

    try:
        from picamera2 import Picamera2
        import face_recognition

        print("[FACE] Starting Raspberry Pi camera...")
        picam2 = Picamera2()

        preview_config = picam2.create_preview_configuration(
            main={"size": (640, 480)}
        )
        picam2.configure(preview_config)
        picam2.start()
        time.sleep(2)

        print("[FACE] Capturing frame...")
        frame = picam2.capture_array()
        picam2.stop()

        # Picamera2 بيرجع الصورة RGB غالبًا، وface_recognition يشتغل عليها عادي
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        if not face_encodings:
            print("[FACE] No face detected")
            return None

        print(f"[FACE] Detected {len(face_encodings)} face(s)")
        print("[FACE] Face found - returning authorized user placeholder")

        # مؤقتًا: أول ما يلاقي وش يرجع أول مستخدم معتمد
        # بعدين نقدر نضيف matching حقيقي بملفات وجوه
        return AUTHORIZED_USERS[0] if AUTHORIZED_USERS else "Authorized User"

    except Exception as e:
        print(f"[FACE] Recognition error: {e}")
        return None


if __name__ == "__main__":
    print("Testing face_rec.py")
    user = identify_user()
    print(f"Detected user: {user}")