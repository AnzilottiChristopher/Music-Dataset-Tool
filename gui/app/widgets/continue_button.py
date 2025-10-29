import tkinter as tk
from tkinter import messagebox
from app.widgets.helper_scripts.check_music_paths import check_consistency
from pathlib import Path

# this will be pressed once we have the json file and the 
class ContinueButton(tk.Frame):
    def __init__(self, parent, on_select=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
       
        # function passed from the window class
        self.on_select = on_select
        self.file_path = None 
        self.folder_path = None 
        
        self.continue_button = tk.Button(
            self,
            text="Continue",
            command=self.continue_pressed,
            fg="white",
            activebackground="#3e3e3e",
            padx=10,
            pady=5   
        )
        
        self.continue_button.pack(pady=10)
    
    def set_file_path(self, path):
        self.file_path = path

    def set_folder_path(self, path):
        self.folder_path = path

    # verify both things exist before advancing
    def continue_pressed(self):
        # uncomment this for quickly skipping to analysis page
        # self.file_path = "/Users/alexpower/Documents/Music-Dataset-Tool/results.json"
        # self.folder_path = "/Users/alexpower/Documents/Music-Dataset-Tool/Music/wav_files"
        
        if not self.file_path or not self.folder_path:
            messagebox.showwarning(
                "Missing selection",
                "Please select both a json file and a folder before continuing."
            )
            return
        
        # add a check here to make sure that all the song_names in the json file have a corresponding
        # song in the folder (if not we should just leave this)
        if not check_consistency(self.file_path, self.folder_path):
            messagebox.showwarning(
                "Songs in the json file were not found in the library",
                "Songs in the json file were not found in the library"
            )
            return
        

        # trigger callback
        if self.on_select:
            self.on_select(self.file_path, self.folder_path)
    
    # here we should loop through all of song names in  
        