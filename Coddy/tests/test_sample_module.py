import pytest
from sample_module import add, get_greeting, Counter

def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_add_negative_numbers():
    assert add(-2, -3) == -5

def test_add_zero():
    assert add(0, 5) == 5
    assert add(5, 0) == 5
    assert add(0,0) == 0

def test_add_mixed_numbers():
    assert add(-2, 3) == 1
    assert add(2, -3) == -1


def test_get_greeting_with_name():
    assert get_greeting("World") == "Hello, World!"

def test_get_greeting_no_name():
    assert get_greeting("") == "Hello, stranger!"
    assert get_greeting(None) == "Hello, stranger!"

def test_get_greeting_with_spaces():
    assert get_greeting("   ") == "Hello, stranger!"
    assert get_greeting(" John ") == "Hello, John !"


def test_counter_increment():
    counter = Counter()
    counter.increment()
    assert counter.get_count() == 1

def test_counter_multiple_increments():
    counter = Counter()
    counter.increment()
    counter.increment()
    counter.increment()
    assert counter.get_count() == 3

def test_counter_initial_count():
    counter = Counter()
    assert counter.get_count() == 0