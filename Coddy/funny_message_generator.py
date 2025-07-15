import random

def generate_funny_message(messages):
    """
    Generates a random funny message from a list of messages.

    Args:
        messages: A list of strings representing funny messages.

    Returns:
        A randomly selected string from the input list.
    """
    if not messages:
        return "No funny messages available."
    return random.choice(messages)

if __name__ == '__main__':
    funny_messages = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Parallel lines have so much in common. It’s a shame they’ll never meet.",
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "I told my wife she was drawing her eyebrows too high. She seemed surprised.",
        "What do you call a fish with no eyes? Fsh!"
    ]
    
    random_message = generate_funny_message(funny_messages)
    print(random_message)