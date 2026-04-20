import speech_recognition as sr
import time


TEST_MODE = False          # خليها True لو عايز تكتب بدل المايك
VOICE_LANGUAGE = "en-US"   # لو عربي خليها "ar-EG"
LISTEN_TIMEOUT = 5
PHRASE_TIME_LIMIT = 6


def speak(text):
    print(f"ORB AI: {text}")


def list_microphones():
    names = sr.Microphone.list_microphone_names()
    print("\n[VOICE] Available microphones:")
    for i, name in enumerate(names):
        print(f"  [{i}] {name}")
    print()
    return names


def choose_mic_index():
    names = sr.Microphone.list_microphone_names()

    if not names:
        print("[VOICE] No microphones found.")
        return None

    # حاول يختار USB Audio Device تلقائيًا
    for i, name in enumerate(names):
        low = name.lower()
        if "usb" in low or "audio" in low or "mic" in low:
            print(f"[VOICE] Auto-selected microphone [{i}]: {name}")
            return i

    print(f"[VOICE] Using default microphone [0]: {names[0]}")
    return 0


def listen():
    if TEST_MODE:
        user_input = input("Type your command: ").strip()
        if not user_input:
            return None
        print(f"[USER]: {user_input}")
        return user_input.lower()

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 200
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    recognizer.non_speaking_duration = 0.5

    mic_index = choose_mic_index()
    if mic_index is None:
        return None

    try:
        with sr.Microphone(device_index=mic_index, sample_rate=16000, chunk_size=1024) as source:
            print(f"[VOICE] Listening on mic index {mic_index} ...")
            print("[VOICE] Stay quiet for 2 seconds for noise calibration...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"[VOICE] Energy threshold = {recognizer.energy_threshold:.2f}")
            print("[VOICE] Speak now...")

            audio = recognizer.listen(
                source,
                timeout=LISTEN_TIMEOUT,
                phrase_time_limit=PHRASE_TIME_LIMIT
            )

        print("[VOICE] Recognizing...")
        text = recognizer.recognize_google(audio, language=VOICE_LANGUAGE)
        print(f"[USER]: {text}")
        return text.lower().strip()

    except sr.WaitTimeoutError:
        print("[VOICE] No speech detected within timeout.")
        return None

    except sr.UnknownValueError:
        print("[VOICE] Speech detected but could not understand.")
        return None

    except sr.RequestError as e:
        print(f"[VOICE] Google recognition service error: {e}")
        return None

    except OSError as e:
        print(f"[VOICE] Microphone OS error: {e}")
        return None

    except Exception as e:
        print(f"[VOICE] Unexpected error: {e}")
        return None


if __name__ == "__main__":
    print("=== ORB Voice Test ===")
    list_microphones()

    while True:
        command = listen()

        if command:
            speak(f"You said: {command}")
        else:
            speak("No valid command detected.")

        again = input("\nPress Enter to test again, or type q to quit: ").strip().lower()
        if again == "q":
            break