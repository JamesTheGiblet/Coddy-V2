Here's a Python code snippet to create a simple GUI window using Tkinter:

```python
import tkinter as tk

# Create main application window
root = tk.Tk()
root.title("My Simple Tkinter Window")

# Set window dimensions (optional)
root.geometry("300x200")

# Add a label (optional)
label = tk.Label(root, text="Hello, Tkinter!")
label.pack(pady=20) # pack() arranges widgets; pady adds vertical padding

# Start the main event loop
root.mainloop()
```

This code creates a window titled "My Simple Tkinter Window" with a label displaying "Hello, Tkinter!".  You can run this directly in a Python interpreter.  Remember to have Tkinter installed (it usually comes with Python).

To make this more useful, tell me what you'd like to *add* to the window.  For example,  buttons, entry fields for user input, different layouts, etc. I can help you build upon this basic framework.
