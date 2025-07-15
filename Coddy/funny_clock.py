import tkinter as tk
import time
import random

def update_time():
    current_time = time.strftime('%H:%M:%S')
    time_label.config(text=current_time)

    messages = [
        "Time to panic!",
        "Still not lunchtime?",
        "Is it Friday yet?",
        "Don't forget to hydrate!",
        "Procrastinate later!",
        "The cake is a lie!",
        "Embrace the chaos!",
        "Where did the time go?",
        "Another minute gone...",
        "Is this real life?"
    ]

    current_minute = int(time.strftime('%M'))
    message_index = current_minute % len(messages)
    message_label.config(text=messages[message_index])

    time_label.after(1000, update_time)

root = tk.Tk()
root.title("Silly Clock")

time_font = ("Comic Sans MS", 48, "bold")
message_font = ("Arial", 20)

time_label = tk.Label(root, font=time_font, bg="white", fg="black")
time_label.pack(pady=50)

message_label = tk.Label(root, font=message_font, bg="white", fg="red", wraplength=500)
message_label.pack()

update_time()

root.mainloop()