```python
# This clock is the best clock ever. Why? Because it tells the time... eventually. And also because I said so.

import tkinter as tk
import time

def update_time():
    """Updates the time displayed on the clock."""
    current_time = time.strftime('%I:%M:%S %p')  # Format the time
    clock_label.config(text=current_time)        # Update the label
    clock_label.after(1000, update_time)        # Call update_time after 1000ms (1 second)


# Create the main window
window = tk.Tk()
window.title("The Best Clock Ever (Probably)")

# Create a label to display the time
clock_label = tk.Label(window, font=('Helvetica', 48), bg='black', fg='cyan')
clock_label.pack(pady=50)  # Add some padding

# Initial call to update the time
update_time()

# Start the Tkinter event loop
window.mainloop()
```
