from config import (
    TEST_MODE,
    VOICE_ENABLED,
    LISTEN_TIMEOUT,
    PHRASE_TIME_LIMIT,
    VOICE_LANGUAGE,
)


def speak(text):
    print(f"ORB AI: {text}")

    if TEST_MODE or not VOICE_ENABLED:
        return

    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.say(text)
        engine.runAndWait()

    except Exception as e:
        print(f"[VOICE] Speak error: {e}")


def listen():
    if TEST_MODE or not VOICE_ENABLED:
        try:
            user_input = input("Type your command: ").strip()
            if not user_input:
                return None
            return user_input.lower()
        except Exception as e:
            print(f"[VOICE] Test input error: {e}")
            return None

    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("Listening for command...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(
                source,
                timeout=LISTEN_TIMEOUT,
                phrase_time_limit=PHRASE_TIME_LIMIT,
            )

        print("Recognizing...")
        query = recognizer.recognize_google(audio, language=VOICE_LANGUAGE)
        print(f"User said: {query}")
        return query.lower().strip()

    except sr.WaitTimeoutError:
        print("[VOICE] Listening timed out")
        return None
    except sr.UnknownValueError:
        print("[VOICE] Could not understand the audio")
        return None
    except sr.RequestError as e:
        print(f"[VOICE] Recognition service error: {e}")
        return None
    except Exception as e:
        print(f"[VOICE] Listen error: {e}")
        return None


if __name__ == "__main__":
    print("Testing voice_assistant.py")
    speak("Voice module test started.")

    command = listen()
    print(f"Returned command: {command}")

    if command:
        speak(f"You typed or said: {command}")
    else:
        speak("No command detected.")
