import tkinter as tk
from app.widgets.file_selector import FileSelector
from app.widgets.music_selector import MusicSelector
from tkinter import messagebox
from app.widgets.helper_scripts.check_music_paths import check_consistency

class SegmentStartPage(tk.Frame):
    def __init__(self, parent, on_continue):
        super().__init__(parent, bg='#1e1e1e')
        self.on_continue = on_continue
        # self.file_path = None
        # self.folder_path = None
        
        # the three lines below should be commented/deleted when we actually analyze 
        self.file_path =  "/Users/alexpower/Documents/Music-Dataset-Tool/results.json"
        self.folder_path = "/Users/alexpower/Documents/Music-Dataset-Tool/Music/wav_files"
        
        # Title
        tk.Label(
            self,
            text="Song Segment Labeling Tool",
            font=("Helvetica", 24, "bold"),
            bg="#1e1e1e",
            fg="white"
        ).pack(pady=30)
        
        
        # File selector
        self.file_selector = FileSelector(self, on_select=self.on_file_selected)
        self.file_selector.pack(pady=20)
        
        # Folder selector
        self.folder_selector = MusicSelector(self, on_select=self.on_folder_selected)
        self.folder_selector.pack(pady=20)
        
        # Continue button
        self.continue_button = tk.Button(
            self,
            text="Start Labeling",
            command=self.continue_pressed,
            bg="#3498db",
            fg="black",
            font=("Helvetica", 14, "bold"),
            padx=30,
            pady=15,
            state="disabled"
        )
        self.continue_button.pack(pady=40)
        
        self.check_ready()
    
    def on_file_selected(self, path):
        print(f"JSON file selected: {path}")
        self.file_path = path
        self.check_ready()
    
    def on_folder_selected(self, path):
        print(f"Folder selected: {path}")
        self.folder_path = path
        self.check_ready()
    
    def check_ready(self):
        """Enable continue button if both paths are selected"""
        if self.file_path and self.folder_path:
            self.continue_button.config(state="normal")
        else:
            self.continue_button.config(state="disabled")
    
    def continue_pressed(self):
        """Verify selections and continue to segment labeling"""
        if not self.file_path or not self.folder_path:
            messagebox.showwarning(
                "Missing Selection",
                "Please select both a JSON file and a folder before continuing."
            )
            return
        
        # Check consistency between JSON and folder
        if not check_consistency(self.file_path, self.folder_path):
            messagebox.showwarning(
                "Inconsistency Error",
                "Some songs in the JSON file were not found in the selected folder.\n"
                "Please ensure all songs referenced in the JSON exist in the folder."
            )
            return
        
        # Proceed to segment labeling
        if self.on_continue:
            self.on_continue(self.file_path, self.folder_path)
