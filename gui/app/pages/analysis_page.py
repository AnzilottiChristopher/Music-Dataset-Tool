import tkinter as tk
from app.widgets.music_player import MusicPlayer
from app.widgets.wave_form import WaveForm
from app.widgets.analyze_button import AnalyzeButton
from app.widgets.helper_scripts.create_transition_audio import create_json_copy
import json 
from pathlib import Path
from tkinter import messagebox
import re


class AnalysisPage(tk.Frame):
    def __init__(self, parent, json_path, folder_path):
        super().__init__(parent, bg="#1e1e1e")
        
        self.json_path = json_path
        self.folder_path = folder_path
        self.transition_audio_files = []
        self.current_index = 0
        self.new_json_path = None
        
        tk.Label(
            self,
            text="Analysis Page",
            font=("Helvetica", 18),
            bg="#1e1e1e",
            fg="white"
        ).pack(pady=20)
        
        self.wave_form = WaveForm(self)
        self.music_player = MusicPlayer(self, waveform=self.wave_form)
        self.analysis_button = AnalyzeButton(
            self,
            json_path=json_path,
            folder_path=folder_path,
            on_complete=self.on_transitions_created
        )
        
        
        
        self.analysis_button.pack(pady=10)
        self.music_player.pack(pady=10)
        self.wave_form.pack(pady=10)
        
        self.song_label = tk.Label(
            self,
            text="",
            font=("Helvetica", 12),
            bg="#1e1e1e",
            fg="#5ad"
        )
        self.song_label.pack(pady=5)
        
        self.rating_frame = tk.Frame(self, bg="#1e1e1e")
        tk.Label(
            self.rating_frame,
            text="Rating (1–10):",
            bg="#1e1e1e",
            fg="white"
        ).pack(side="left", padx=5)
        
        self.rating_entry = tk.Spinbox(self.rating_frame, from_=1, to=10, width=5)
        self.rating_entry.pack(side="left", padx=5)
        
        self.comment_box = tk.Text(self.rating_frame, height=3, width=40)
        self.comment_box.pack(padx=5, pady=10)
        
        self.submit_button = tk.Button(
            self.rating_frame,
            text="Submit Rating",
            command=self.submit_rating,
            bg="#2e2e2e",
            fg="black"
        )
        self.submit_button.pack(pady=5)
        
        self.rating_frame.pack_forget()  
    
    # called when transitions done computing
    def on_transitions_created(self, transition_audio_path):
        self.new_json_path = create_json_copy(self.json_path)
        self.transition_audio_files = sorted(Path(transition_audio_path).glob("*.wav"))
        if not self.transition_audio_files:
            messagebox.showerror("Error", "No transition files found.")
            return
        
        messagebox.showinfo("Ready", f"{len(self.transition_audio_files)} transitions found.")
        self.rating_frame.pack(pady=15)
        self.load_next_audio()
    
    def load_next_audio(self):
        if self.current_index >= len(self.transition_audio_files):
            messagebox.showinfo("Done", "All transitions rated!")
            return
        
        audio_path = str(self.transition_audio_files[self.current_index])
        file_name = self.transition_audio_files[self.current_index].name

        # New pattern for segment-based transitions
        pattern = r'(.*?)-TO-(.*?)-([\w-]+)-to-([\w-]+)\.wav'
        match = re.match(pattern, file_name)
        
        if match:
            first_song, second_song, exit_segment, entry_segment = match.groups()
            self.song_label.config(text=f"{first_song} ({exit_segment}) → {second_song} ({entry_segment})")
        else:
            self.song_label.config(text=file_name)
        
        self.music_player.load_music(audio_path)
        self.wave_form.load_audio(audio_path)
        self.comment_box.delete("1.0", tk.END)
        self.rating_entry.delete(0, tk.END)
        self.rating_entry.insert(0, "5") 
    
    def submit_rating(self):
        rating = self.rating_entry.get()
        comment = self.comment_box.get("1.0", tk.END).strip()
        file_name = self.transition_audio_files[self.current_index].name
        
        try:
            with open(self.new_json_path, "r+") as f:
                data = json.load(f)
                if "transitions" not in data:
                    data["transitions"] = []
                
                # Fixed pattern to handle hyphens in segment names
                pattern = r'(.*?)-TO-(.*?)-([\w-]+)-to-([\w-]+)\.wav'
                match = re.match(pattern, file_name)
                
                if not match:
                    messagebox.showerror("Error", f"Could not parse filename: {file_name}")
                    return
                
                first_song, second_song, exit_segment, entry_segment = match.groups()
                
                transition_entry = {
                    "song_a": first_song,
                    "song_b": second_song,
                    "exit_segment": exit_segment,
                    "entry_segment": entry_segment,
                    "rating": int(rating),
                    "comment": comment,
                }
                
                
                data["transitions"].append(transition_entry)
                
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
                
                print(f"[INFO] Saved rating for {exit_segment} -> {entry_segment}: {rating}/10")
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not write to JSON: {e}")
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return
        
        self.current_index += 1
        self.load_next_audio()

        
        
        
        
        