import time
from datetime import datetime

import face_rec
import voice_assistant
import led_control

from config import MAX_VOICE_RETRIES


def process_command(command, current_user=None):
    command = command.lower().strip()

    led_control.show_processing_light()

    if "temperature" in command or "hot" in command:
        response = "It seems warm. I will turn on the air conditioner for you."

    elif "light" in command or "lights" in command:
        response = "Sure, turning the lights on now."

    elif "who am i" in command:
        if current_user:
            response = f"You are {current_user}, my authorized boss."
        else:
            response = "I cannot identify you right now."

    elif "hello" in command or "hi" in command:
        if current_user:
            response = f"Hello {current_user}, how can I help you?"
        else:
            response = "Hello, how can I help you?"

    elif "time" in command:
        current_time = datetime.now().strftime("%I:%M %p")
        response = f"The current time is {current_time}"

    elif "your name" in command:
        response = "I am ORB AI, your smart assistant."

    elif "how are you" in command:
        response = "I am functioning perfectly."

    elif command in ["stop", "exit", "quit"]:
        return "shutdown"

    else:
        led_control.show_error_light()
        response = "I heard you, but I am not sure how to help with that yet."

    led_control.show_speaking_light()
    voice_assistant.speak(response)

    return "continue"


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
                voice_assistant.speak(
                    "I am having trouble hearing you. Shutting down now."
                )
                break

            continue

        fail_count = 0

        result = process_command(command, current_user=user_name)

        if result == "shutdown":
            led_control.show_speaking_light()
            voice_assistant.speak("Goodbye!")
            led_control.turn_off()
            break

        led_control.show_idle_light()
        time.sleep(0.5)


if __name__ == "__main__":
    startup_orb()
