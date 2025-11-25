import tkinter as tk
from tkinter import filedialog


class FileSelector(tk.Frame):
    def __init__(self, parent, on_select=None, label_text="Select JSON File", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(bg="#000000")
        
        self.on_select = on_select # this will be a function
        self.selected_file = None 
        
        self.select_button = tk.Button(
            self,
            text=label_text,
            command=self.select_json_file,
            bg="#2e2e2e",
            fg="black",
            activebackground="#3e3e3e",
            padx=10,
            pady=5
        )
        self.select_button.pack(pady=10)

        # this should show the path
        self.file_label = tk.Label(
            self,
            text="No file selected",
            bg="#1e1e1e",
            fg="#ffffff",
            wraplength=500
        )
        self.file_label.pack(pady=5)

        
    def select_json_file(self):
        file_path = filedialog.askopenfilename(
            title="Select JSON file",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=f"Selected file:\n{file_path}")

            if self.on_select:
                self.on_select(file_path)
        else:
            self.file_label.config(text="No file selected")
    
    # this will be need for verification     
    def get_file(self):
        if self.selected_file is None:
            print(f"no file was selected")
        else:
            return self.selected_file