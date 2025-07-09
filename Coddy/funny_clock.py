
import tkinter as tk
from tkinter import font
import time

def funny_gui_clock():
    root = tk.Tk()
    root.title("Funny Clock")
    root.geometry("400x200")
    root.resizable(False, False)
    root.configure(bg='#282c34') # Dark background

    # Custom font for a "funny" look, or just a large, clear one
    clock_font = font.Font(family="Helvetica", size=48, weight="bold")
    
    time_label = tk.Label(
        root,
        font=clock_font,
        bg='#282c34',
        fg='#00e5ff' # Neon blue
    )
    time_label.pack(expand=True)

    def update_time():
        current_time = time.strftime("%H:%M:%S")
        # Add some "funny" emojis or characters based on time
        funny_char = ""
        if int(time.strftime("%S")) % 5 == 0:
            funny_char = "😂"
        elif int(time.strftime("%S")) % 3 == 0:
            funny_char = "⏰"
        
        time_label.config(text=f"{current_time} {funny_char}")
        root.after(1000, update_time) # Update every 1000ms (1 second)

    update_time()
    root.mainloop()

if __name__ == "__main__":
    funny_gui_clock()
