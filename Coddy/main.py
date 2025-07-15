import datetime
import random

class FunnyClock:
    def __init__(self, current_time=None):
        if current_time is None:
            self.current_time = datetime.datetime.now()
        else:
            self.current_time = current_time
        self.phrases = {
            "%H:%M": ["Time for adventure!", "Seize the day!", "Make it count!"],
            "%I:%M %p": ["Laugh o'clock!", "Giggle time!", "Chuckles galore!"],
            "%A, %B %d": ["A day for shenanigans!", "Embrace the chaos!", "Let's get silly!"],
            "%Y-%m-%d %H:%M:%S": ["Tick-tock, party rock!", "Time flies when you're having fun!", "Don't stop the beat!"]
        }
        self.jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Parallel lines have so much in common. It’s a shame they’ll never meet.",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "Why did the bicycle fall over? Because it was two tired!",
            "What do you call a fish with no eyes? Fsh!"
        ]

    def get_time(self, format_string):
        time_str = self.current_time.strftime(format_string)
        if format_string in self.phrases:
            phrase = random.choice(self.phrases[format_string])
            return f"{time_str} - {phrase}"
        else:
            return time_str

    def tell_a_joke(self):
        return random.choice(self.jokes)


if __name__ == "__main__":
    clock = FunnyClock()

    print("Current Time:")
    print(clock.get_time("%H:%M"))
    print(clock.get_time("%I:%M %p"))
    print(clock.get_time("%A, %B %d"))
    print(clock.get_time("%Y-%m-%d %H:%M:%S"))

    joke = clock.tell_a_joke()
    print("\nHere's a joke for you:")
    print(joke)