import tkinter as tk
import pygame

# this will represent the actual music playing button to play the recorded transition
class MusicPlayer(tk.Frame):
    def __init__(self, parent, waveform=None):
        super().__init__(parent, bg="#1e1e1e")
        
        pygame.mixer.init()
        
        self.current_audio = None 
        self.is_playing = False
        self.wave_form= waveform
        
        
        button_frame = tk.Frame(self, bg="#1e1e1e")
        button_frame.pack(pady=5)

        self.play_button = tk.Button(
            self,
            text="Play",
            command=self.play_music,
            bg="#2e2e2e",
            fg="black",
            padx=10,
            pady=5
        )
        self.play_button.pack(side="left", padx=5)

        self.stop_button = tk.Button(
            self,
            text="Stop/Restart",
            command=self.stop_music,
            bg="#2e2e2e",
            fg="black",
            padx=10,
            pady=5
        )
        self.stop_button.pack(side='right', padx=5)

        
    def load_music(self, path):
        self.current_audio = path 
        pygame.mixer.music.load(path)
        
    def play_music(self):
        if not self.current_audio:
            print('No music file was loaded')
            return
        
        # Stop any currently playing music first
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        # Small delay to ensure music fully stops
        pygame.time.wait(50)
        
        # Reload and play the music
        pygame.mixer.music.load(self.current_audio)
        pygame.mixer.music.play()
        self.is_playing = True
        
        if self.wave_form:
            self.wave_form.start_playhead()
        
    def stop_music(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        
        if self.wave_form:
            self.wave_form.stop_playhead()
        
        
        
        