from datetime import datetime


def generate_response(command, current_user=None):
    command = command.lower().strip()

    if "temperature" in command or "hot" in command:
        return "It seems warm. I will turn on the air conditioner for you."

    elif "light on " in command or "lights on" in command:
        return "Sure, turning the lights on now."

    elif "light off " in command or "lights off" in command:
        return "Sure, turning the lights off now."

    elif "who am i" in command:
        if current_user:
            return f"You are {current_user}, my authorized boss."
        return "I cannot identify you right now."

    elif "hello" in command or "hi" in command:
        if current_user:
            return f"Hello {current_user}, how can I help you?"
        return "Hello, how can I help you?"

    elif "time" in command:
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}"

    elif "your name" in command:
        return "I am ORB_AI, here to help you with various tasks."

    elif "how are you" in command:
        return "I'm just a program, but I'm functioning as expected. Thanks for asking!"

    elif "stop" in command or "exit" in command or "quit" in command:
        return "shutdown"

    elif "cold" in command or "cool" in command:
        return "It seems cool. I will turn off the air conditioner for you."

    elif "date" in command:
        return f"Today's date is {datetime.now().strftime('%B %d, %Y')}"

    else:
        return "I heard you, but I am not sure how to help with that yet."


if __name__ == "__main__":
    test_commands = [
        "What is your name?",
        "How are you?",
        "What is the time?",
        "Turn on the lights",
        "What is the temperature?",
        "Who am I?",
        "Hello",
        "Exit",
    ]

    for cmd in test_commands:
        print(f"Command: {cmd}")
        print(f"Response: {generate_response(cmd, current_user='karim')}")
        print("-" * 30)
