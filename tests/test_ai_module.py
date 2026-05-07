from response_generator import ResponseGenerator, generate_response


def test_greeting_intent_names_user():
    response = ResponseGenerator().generate("hello orb", current_user="Karim")

    assert response.intent.name == "greeting"
    assert "Karim" in response.text


def test_time_intent():
    response = ResponseGenerator().generate("what is the time")

    assert response.intent.name == "current_time"
    assert "current time" in response.text.lower()


def test_system_status_intent():
    response = ResponseGenerator().generate("system status")

    assert response.intent.name == "system_status"
    assert "system online" in response.text.lower()


def test_shutdown_compatibility_response():
    assert generate_response("exit") == "shutdown"
