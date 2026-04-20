import time

import face_rec
import voice_assistant
import led_control
import assistant_brain

from config import MAX_VOICE_RETRIES


def startup_orb():
    print("ORB AI System Starting...")

    led_control.init_led()
    led_control.show_startup_light()
    time.sleep(1)

    user_name = face_rec.identify_user()

    if user_name:
        led_control.show_success_light()
        voice_assistant.speak(f"Hello {user_name}, I am online and ready.")
    else:
        led_control.show_error_light()
        voice_assistant.speak("Face not recognized. Entering guest mode.")
        user_name = None

    fail_count = 0

    while True:
        led_control.show_listening_light()
        command = voice_assistant.listen()

        if not command:
            fail_count += 1
            print(f"[SYSTEM] Failed listen attempt: {fail_count}")

            if fail_count >= MAX_VOICE_RETRIES:
                led_control.show_error_light()
                voice_assistant.speak("I am having trouble hearing you. Shutting down now.")
                break

            continue

        fail_count = 0
        print(f"[SYSTEM] Command received: {command}")

        led_control.show_processing_light()
        response = assistant_brain.generate_response(command, current_user=user_name)

        if response == "shutdown":
            led_control.show_speaking_light()
            voice_assistant.speak("Goodbye!")
            led_control.turn_off()
            break

        led_control.show_speaking_light()
        voice_assistant.speak(response)

        led_control.show_idle_light()
        time.sleep(0.5)


if __name__ == "__main__":
    startup_orb()