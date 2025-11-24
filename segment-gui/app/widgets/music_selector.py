import tkinter as tk
from tkinter import filedialog


class MusicSelector(tk.Frame):
    def __init__(self, parent, on_select=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(bg="#000000")
        
        self.on_select = on_select # this will be a function
        self.selected_folder = None
        
        
        self.select_button = tk.Button(
            self,
            text="Select folder",
            command=self.select_folder,
            bg="#2e2e2e",
            fg="black",
            activebackground="#3e3e3e",
            padx=10,
            pady=5
        )
        self.select_button.pack(pady=10)

        # this should show the path
        self.folder_label = tk.Label(
            self,
            text="No folder selected",
            bg="#1e1e1e",
            fg="#ffffff",
            wraplength=500
        )
        self.folder_label.pack(pady=5)
        
    def select_folder(self):
        file_path = filedialog.askdirectory(
            title="Select folder"
        )
        
        # file_path = "/Users/alexpower/Documents/Music-Dataset-Tool/Music/wav_files"

        if file_path:
            self.selected_file = file_path
            self.folder_label.config(text=f"Selected folder:\n{file_path}")

            if self.on_select:
                self.on_select(file_path)
        else:
            self.folder_label.config(text="No folder selected") 
            
    def get_path(self):
        if self.selected_folder is None:
            print("there was no folder selected, look into this")
        else:
            return self.selected_folder