import unittest
from unittest.mock import patch
import datetime
import random

class FunnyClock:
    def __init__(self, hour=None, minute=None):
        self.hour = hour if hour is not None else random.randint(0, 23)
        self.minute = minute if minute is not None else random.randint(0, 59)

    def strftime(self, format_string):
        dt = datetime.datetime(2024, 1, 1, self.hour, self.minute)
        return dt.strftime(format_string)

    def tell_a_joke(self):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Parallel lines have so much in common. It’s a shame they’ll never meet.",
            "Why did the scarecrow win an award? Because he was outstanding in his field!"
        ]
        return random.choice(jokes)

class TestFunnyClock(unittest.TestCase):

    def test_initialization(self):
        try:
            FunnyClock()
        except Exception as e:
            self.fail(f"FunnyClock initialization failed: {e}")

    def test_strftime_returns_string(self):
        clock = FunnyClock(hour=10, minute=30)
        result = clock.strftime("%H:%M")
        self.assertIsInstance(result, str)

    def test_tell_a_joke_returns_string(self):
        clock = FunnyClock()
        result = clock.tell_a_joke()
        self.assertIsInstance(result, str)


if __name__ == '__main__':
    unittest.main()