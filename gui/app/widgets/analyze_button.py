import tkinter as tk
from app.widgets.helper_scripts.create_transition_audio import compute_transition_audio
from tkinter import messagebox
import os,sys, json
from pathlib import Path
import shutil

class AnalyzeButton(tk.Frame):
    def __init__(self, parent, json_path, folder_path, on_complete=None):
        super().__init__(parent)
        
        self.on_complete = on_complete
        self.json_path = json_path
        self.folder_path = folder_path 
        
        self.analyze_button = tk.Button(
            self,
            text="Begin Analysis",
            command=self.analyze_pressed,
            fg="black",
            activebackground="#3e3e3e",
            padx=10,
            pady=5   
        )
        
        self.analyze_button.pack(pady=10)
        
        
    # so now, we loop through the json, get boths songs, and load them.
    # then for each phrase boundary compute the transition clips
    # so if there are n^2 phrase boundaries, then we have n^2 to rank for each song
    # so each song pair generates 2*(n^2) rankings, then move on down the list changing song a 
    def analyze_pressed(self):
        # data is the original json, new path is the new folder path the new file is saved at (where to write to)
        # maybe should return the new json path to modify for us
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        
        original_folder_path = Path(self.folder_path)
        
        new_folder_name = "transition_files"
        new_folder_path = original_folder_path.parent / new_folder_name
        
        if new_folder_path.exists():
            shutil.rmtree(new_folder_path)
        
        new_folder_path.mkdir(parents=True)
        
        
        messagebox.showinfo(
            title='"Analysis will now begin."',
            message="depending on the length of songs, this may take a while"
        )
        
        song_array = data['songs']
        for i, song_a in enumerate(song_array):
            for j, song_b in enumerate(song_array):
                
                # skip matching songs with eachother and ones we have already computed.
                if i <= j:
                    continue
                
                # now we compute all new audio files in song_a
                exit_boundaries_a = song_a['features']['last_phrase_boundaries']
                entry_boundaries_b = song_b['features']['first_phrase_boundaries']
                
                for exit_boundary in exit_boundaries_a:
                    for entry_boundary in entry_boundaries_b:
                        
                        exit_time = self._time_to_secs(exit_boundary)
                        entry_time = self._time_to_secs(entry_boundary)
                        
                        song_a_path = os.path.join(self.folder_path, song_a['song_name'])
                        song_b_path = os.path.join(self.folder_path, song_b['song_name'])
                        
                        audio_file_name = f"{song_a['song_name']}-TO-{song_b['song_name']}-exit{exit_time}-entry{entry_time}.wav"
                        
                        output_path = new_folder_path / audio_file_name
                        
                        _ = compute_transition_audio(song_a=song_a_path, song_b=song_b_path, time_a=exit_time,
                                                     time_b=entry_time, output_path=output_path)
                        
                # NOW WE GO THE OTHER WAY, ESSENTIALLY COPYING WHAT WE HAVE DONE HERE
                exit_boundaries_b = song_b['features']['last_phrase_boundaries']
                entry_boundaries_a = song_a['features']['first_phrase_boundaries']
                
                for exit_boundary in exit_boundaries_b:
                    for entry_boundary in entry_boundaries_a:
                        
                        exit_time = self._time_to_secs(exit_boundary)
                        entry_time = self._time_to_secs(entry_boundary)
                        
                        song_a_path = os.path.join(self.folder_path, song_b['song_name'])
                        song_b_path = os.path.join(self.folder_path, song_a['song_name'])
                        
                        audio_file_name = f"{song_b['song_name']}-TO-{song_a['song_name']}-exit{exit_time}-entry{entry_time}.wav"
                        
                        output_path = new_folder_path / audio_file_name
                        
                        _ = compute_transition_audio(song_a=song_a_path, song_b=song_b_path, time_a=exit_time,
                                                     time_b=entry_time, output_path=output_path)
                        
                        
        if callable(self.on_complete):
            self.on_complete(new_folder_path)
                        
    def _time_to_secs(self, time):
        str_representation = str(time)
        minutes, seconds = str_representation.split(':')
        
        minutes = minutes[1]
        
        return float((int(minutes) * 60) + (int(seconds)))
    
    
    
    
