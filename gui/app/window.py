# this will serve as the main window

import tkinter as tk
from app.widgets.file_selector import FileSelector

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dataset Creation Tool")
        self.root.geometry("800x600")
        
        self.root.configure(bg="#ffffff") # white background, change to what we want
        self.file_selector = FileSelector(self.root, on_select=self.on_file_selected)
        self.file_selector.pack(pady=40)
        
    # just to test
    def on_file_selected(self, path):
        print(f"user selected JSON file: {path}")
        
    def run(self):
        print('App is now running') # so this is not running
        self.root.mainloop()