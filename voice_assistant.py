from config import (
    TEST_MODE,
    VOICE_ENABLED,
    LISTEN_TIMEOUT,
    PHRASE_TIME_LIMIT,
    VOICE_LANGUAGE,
)


def speak(text):
    print(f"[ORB SPEAK] {text}")

    if TEST_MODE or not VOICE_ENABLED:
        return

    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.say(text)
        engine.runAndWait()

    except Exception as e:
        print(f"[VOICE ERROR] Speak error: {e}")


def listen():
    #  TEST MODE (Simulation)
    if TEST_MODE or not VOICE_ENABLED:
        try:
            command = input("🎤 Type command: ").strip()
            if not command:
                print("[VOICE] Empty input")
                return None

            print(f"[VOICE DEBUG] Typed: {command}")
            return command.lower()

        except Exception as e:
            print(f"[VOICE ERROR] Test input error: {e}")
            return None

    #  REAL MICROPHONE MODE
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("[VOICE] Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            audio = recognizer.listen(
                source,
                timeout=LISTEN_TIMEOUT,
                phrase_time_limit=PHRASE_TIME_LIMIT,
            )

        print("[VOICE] Recognizing...")
        query = recognizer.recognize_google(audio, language=VOICE_LANGUAGE)

        print(f"[VOICE DEBUG] Heard: {query}")
        return query.lower().strip()

    except sr.WaitTimeoutError:
        print("[VOICE WARNING] Listening timed out")
        return None

    except sr.UnknownValueError:
        print("[VOICE WARNING] Could not understand audio")
        return None

    except sr.RequestError as e:
        print(f"[VOICE ERROR] Recognition service error: {e}")
        return None

    except Exception as e:
        print(f"[VOICE ERROR] Listen error: {e}")
        return None


if __name__ == "__main__":
    print("Testing voice_assistant.py")

    while True:
        cmd = listen()
        print(f"[TEST RESULT] {cmd}")

        if cmd == "exit":
            break

        speak(f"You said: {cmd}")
