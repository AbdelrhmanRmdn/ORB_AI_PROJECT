import time

import face_rec
import voice_assistant
import led_control
import assistant_brain

from config import MAX_VOICE_RETRIES


def startup_orb():
    print(" ORB AI System Starting...")

    led_control.init_led()
    led_control.show_startup_light()
    time.sleep(1)

    print("[SYSTEM] Identifying user...")
    user_name = face_rec.identify_user()

    if user_name:
        print(f"[SYSTEM] User recognized: {user_name}")
        led_control.show_success_light()
        voice_assistant.speak(f"Hello {user_name}, I am online and ready.")
    else:
        print("[SYSTEM] Unknown user")
        led_control.show_error_light()
        voice_assistant.speak("Face not recognized. Entering guest mode.")
        user_name = None

    fail_count = 0

    while True:
        print("\n[SYSTEM] Waiting for command...")
        led_control.show_listening_light()

        command = voice_assistant.listen()

        #  No input
        if not command:
            fail_count += 1
            print(f"[SYSTEM WARNING] Failed listen attempt: {fail_count}")

            if fail_count >= MAX_VOICE_RETRIES:
                print("[SYSTEM ERROR] Too many failed attempts")
                led_control.show_error_light()
                voice_assistant.speak(
                    "I am having trouble hearing you. Shutting down now."
                )
                break

            continue

        #  Valid input
        fail_count = 0
        print(f"[SYSTEM DEBUG] Command received: {command}")

        led_control.show_processing_light()

        response = assistant_brain.generate_response(command, current_user=user_name)

        print(f"[SYSTEM DEBUG] Response: {response}")

        #  Shutdown
        if response == "shutdown":
            print("[SYSTEM] Shutting down...")
            led_control.show_speaking_light()
            voice_assistant.speak("Goodbye!")
            led_control.turn_off()
            break

        #  Normal response
        led_control.show_speaking_light()
        time.sleep(0.5)  # simulate thinking
        voice_assistant.speak(response)

        led_control.show_idle_light()
        time.sleep(0.5)


if __name__ == "__main__":
    startup_orb()
