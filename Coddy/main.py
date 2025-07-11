This task requires several components. I can't create a fully functional GUI application within this response due to the limitations of this text-based interface.  However, I can provide you with a structured Python code outline and explanations of the key parts, which you can then integrate using a GUI framework like Tkinter, PyQt, or Kivy.

This example uses Tkinter for its simplicity.  You'll need to install it if you don't already have it (`pip install tkinter`).

```python
import tkinter as tk
import time
import random

# --- Clock Core ---
def update_clock():
    current_time = time.strftime("%H:%M:%S")
    clock_label.config(text=current_time)
    clock_label.after(1000, update_clock)  # Update every second

# --- Funny Phrase, Font, and Color Selectors ---
phrases = [
    "Hello, world!",
    "Python is awesome!",
    "Keep calm and code on!",
    "Debugging is a journey, not a destination.",
    "May your coffee be strong and your bugs be few."
]

fonts = ["Arial", "Times New Roman", "Courier", "Helvetica"]
colors = ["red", "green", "blue", "yellow", "purple"]

def change_phrase():
    new_phrase = random.choice(phrases)
    phrase_label.config(text=new_phrase)

def change_font():
    new_font = random.choice(fonts)
    phrase_label.config(font=new_font)

def change_color():
    new_color = random.choice(colors)
    phrase_label.config(fg=new_color) # fg changes the text color


# --- GUI ---
root = tk.Tk()
root.title("Clock & Funny Phrase App")

# Clock
clock_label = tk.Label(root, font=("Helvetica", 48), text="")
clock_label.pack(pady=20)
update_clock()

# Phrase
phrase_label = tk.Label(root, text=random.choice(phrases), font=("Arial", 24))
phrase_label.pack(pady=10)

# Buttons
phrase_button = tk.Button(root, text="New Phrase", command=change_phrase)
phrase_button.pack(pady=5)

font_button = tk.Button(root, text="New Font", command=change_font)
font_button.pack(pady=5)

color_button = tk.Button(root, text="New Color", command=change_color)
color_button.pack(pady=5)


root.mainloop()
```

This code provides:

* **Clock Core:**  The `update_clock` function continuously updates the time display.
* **Funny Phrase, Font, and Color Selectors:**  Lists of phrases, fonts, and colors are used, and functions randomly select and apply them.
* **GUI (Tkinter):**  A simple Tkinter GUI integrates the clock and the phrase display with buttons to change the phrase, font and color.

Remember to expand this code to include more sophisticated features, error handling, and potentially a more visually appealing design using  Tkinter's layout managers (like `grid` or `place`) for better control over the GUI's appearance.  Consider exploring other GUI frameworks like PyQt or Kivy for more advanced features and customization options.
