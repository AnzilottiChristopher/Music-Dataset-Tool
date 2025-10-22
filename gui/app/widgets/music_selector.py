import tkinter as tk
from tkinter import filedialog


class MusicSelector(tk.Frame):
    def __init__(self, parent, on_select=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(bg="#000000")
        
        