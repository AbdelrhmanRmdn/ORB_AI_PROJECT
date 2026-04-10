from datetime import datetime


def generate_response(command, current_user=None):
    command = command.lower().strip()

    #  TEMPERATURE
    if any(word in command for word in ["cold", "cool"]):
        return "It seems cool. I will turn off the air conditioner."

    elif any(word in command for word in ["hot", "warm"]):
        return "It seems warm. I will turn on the air conditioner."

    #  LIGHT CONTROL
    elif "light" in command or "lights" in command:
        if "on" in command:
            return "Turning on the lights."

        elif "off" in command:
            return "Turning off the lights."

        else:
            return "Do you want me to turn the lights on or off?"

    #  USER IDENTIFICATION
    elif "who am i" in command:
        if current_user:
            return f"You are {current_user}, my authorized boss."
        return "I cannot identify you right now."

    #  GREETINGS
    elif any(word in command for word in ["hello", "hi", "hey"]):
        if current_user:
            return f"Hello {current_user}, how can I help you?"
        return "Hello, how can I help you?"

    #  PERSONALITY
    elif "your name" in command:
        return "I am ORB AI, here to help you."

    elif "how are you" in command:
        return "I am functioning perfectly."

    #  TIME & DATE
    elif "time" in command:
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}"

    elif "date" in command:
        today = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today's date is {today}"

    #  EXIT
    elif any(word in command for word in ["stop", "exit", "quit"]):
        return "shutdown"

    #  UNKNOWN
    else:
        return "I heard you, but I am not sure how to help with that yet."


if __name__ == "__main__":
    test_commands = [
        "what is your name",
        "how are you",
        "what is the time",
        "turn on the lights",
        "turn off the lights",
        "it is cold",
        "it is hot",
        "what is the date",
        "who am i",
        "hello",
        "exit",
    ]

    for cmd in test_commands:
        print(f"Command: {cmd}")
        print(f"Response: {generate_response(cmd, current_user='karim')}")
        print("-" * 30)
