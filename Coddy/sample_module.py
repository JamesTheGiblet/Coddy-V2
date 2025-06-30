# c:/Users/gilbe/Documents/GitHub/Coddy V2/Coddy/sample_module.py

def add(a, b):
    """Adds two numbers together."""
    return a + b

def get_greeting(name: str) -> str:
    """Returns a greeting string."""
    if not name or not name.strip():
        return "Hello, stranger!"
    return f"Hello, {name.strip()}!"

class Counter:
    """A simple counter class."""
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1

    def get_count(self):
        return self.count
