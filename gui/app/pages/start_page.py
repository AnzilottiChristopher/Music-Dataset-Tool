import tkinter as tk
from app.widgets.file_selector import FileSelector
from app.widgets.music_selector import MusicSelector
from app.widgets.continue_button import ContinueButton


class StartPage(tk.Frame):
    def __init__(self, parent, on_continue):
        super().__init__(parent, bg='#ffffff')
        self.on_continue = on_continue
         
        self.file_selector = FileSelector(self, on_select=self.on_file_selected)
        self.file_selector.pack(pady=40)
        
        # folder selector
        self.folder_selector = MusicSelector(self, on_select=self.on_folder_selected)
        self.folder_selector.pack(pady=40)
        
        self.continue_button = ContinueButton(self, on_select=self.on_continue)
        self.continue_button.pack(pady=40)
        
        
    # just to test
    def on_file_selected(self, path):
        print(f"user selected JSON file: {path}")
        self.continue_button.set_file_path(path)
        
    def on_folder_selected(self, path):
        print(f"User selected folder {path}")
        self.continue_button.set_folder_path(path)
        
    def on_continue(self, file_path, folder_path):
        print("[INFO] Continuing with:")
        print(f"File:   {file_path}")
        print(f"Folder: {folder_path}")

        # clear the screen or open the next view
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(
            self.root,
            text="Next window loaded!",
            bg="#1e1e1e",
            fg="white",
            font=("Helvetica", 16)
        ).pack(expand=True)