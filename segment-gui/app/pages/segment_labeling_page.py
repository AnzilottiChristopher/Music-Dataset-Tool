import tkinter as tk
from tkinter import messagebox, ttk
import json
from pathlib import Path
import pygame

class SegmentLabelingPage(tk.Frame):
    def __init__(self, parent, json_path, folder_path, output_json_path=None, on_complete=None):
        super().__init__(parent, bg="#1e1e1e")
        
        self.json_path = json_path
        self.folder_path = folder_path
        self.output_json_path = output_json_path
        self.on_complete = on_complete
        self.current_song_index = 0
        self.songs_data = []
        self.completed_songs = set()  # Track which songs are already labeled
        self.current_segments = []
        self.new_json_path = None
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0  # Position in seconds
        self.pause_position = 0  # Where we paused in seconds
        
        # Segment types and their colors
        self.segment_types = {
            "intro": "#FF6B6B",
            "verse": "#4ECDC4",
            "chorus": "#45B7D1",
            "build-up": "#96CEB4",
            "beat-drop": "#FECA57",
            "cool-down": "#9C88FF",
            "outro": "#FD79A8",
            "bridge": "#A29BFE",
            "breakdown": "#6C5CE7",
            "other": "#95A5A6"
        }
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Load songs from JSON
        self.load_songs_data()
        
        # Create UI
        self.setup_ui()
        
        # Load first unlabeled song
        if self.songs_data:
            self.find_next_unlabeled_song()
    
    def load_songs_data(self):
        """Load the JSON data and prepare for editing"""
        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
                self.songs_data = data.get('songs', [])
            
            # If output JSON provided, load it and check which songs are already done
            if self.output_json_path and Path(self.output_json_path).exists():
                print(f"Loading existing output from: {self.output_json_path}")
                with open(self.output_json_path, 'r') as f:
                    output_data = json.load(f)
                    output_songs = output_data.get('songs', [])
                    
                    # Identify which songs already have segments
                    for song in output_songs:
                        segments = song.get('segments', {})
                        if segments and len(segments) > 0:
                            self.completed_songs.add(song['song_name'])
                            print(f"  - {song['song_name']} already labeled (skipping)")
                
                # Use the existing output file
                self.new_json_path = self.output_json_path
                print(f"Found {len(self.completed_songs)} already-labeled songs")
            else:
                # Create a new output file
                self.new_json_path = Path(self.json_path).parent / f"segmented_{Path(self.json_path).name}"
                with open(self.new_json_path, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Created new output file: {self.new_json_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON: {e}")
    
    def find_next_unlabeled_song(self):
        """Find the next song that hasn't been labeled yet"""
        while self.current_song_index < len(self.songs_data):
            song = self.songs_data[self.current_song_index]
            song_name = song['song_name']
            
            if song_name not in self.completed_songs:
                # Found an unlabeled song
                self.load_current_song()
                return
            else:
                # This song is already done, skip to next
                print(f"Skipping already-labeled song: {song_name}")
                self.current_song_index += 1
        
        # If we get here, all songs are labeled
        messagebox.showinfo("Complete", "All songs have been labeled!")
        self.finish_labeling()
    
    def setup_ui(self):
        """Setup the main UI components"""
        
        # Title and song info
        self.title_label = tk.Label(
            self,
            text="Segment Labeling Tool",
            font=("Helvetica", 20, "bold"),
            bg="#1e1e1e",
            fg="white"
        )
        self.title_label.pack(pady=10)
        
        self.song_info_label = tk.Label(
            self,
            text="",
            font=("Helvetica", 14),
            bg="#1e1e1e",
            fg="#5ad"
        )
        self.song_info_label.pack(pady=5)
        
        # Progress indicator with completed count
        self.progress_label = tk.Label(
            self,
            text="",
            font=("Helvetica", 10),
            bg="#1e1e1e",
            fg="#888"
        )
        self.progress_label.pack(pady=2)
        
        # Import the enhanced WaveForm widget
        from app.widgets.wave_form import WaveForm
        
        # Waveform with timeline
        self.waveform_frame = tk.Frame(self, bg="#1e1e1e")
        self.waveform_frame.pack(pady=10, padx=20, fill="x")
        
        self.waveform = WaveForm(
            self.waveform_frame,
            width=750,
            height=150,
            bg="#2a2a2a"
        )
        self.waveform.pack()
        # Set the seek callback for scrubbing
        self.waveform.set_seek_callback(self.seek_to)
        
        # Timeline under waveform
        self.timeline_canvas = tk.Canvas(
            self.waveform_frame,
            width=750,
            height=30,
            bg="#1e1e1e",
            highlightthickness=0
        )
        self.timeline_canvas.pack()
        
        # Playback controls
        self.playback_frame = tk.Frame(self, bg="#1e1e1e")
        self.playback_frame.pack(pady=10)
        
        self.play_button = tk.Button(
            self.playback_frame,
            text="▶ Play",
            command=self.toggle_playback,
            bg="#2e2e2e",
            fg="black",
            padx=20,
            pady=10,
            font=("Helvetica", 12)
        )
        self.play_button.pack(side="left", padx=5)
        
        self.stop_button = tk.Button(
            self.playback_frame,
            text="■ Stop",
            command=self.stop_playback,
            bg="#2e2e2e",
            fg="black",
            padx=20,
            pady=10,
            font=("Helvetica", 12)
        )
        self.stop_button.pack(side="left", padx=5)
        
        # Time display
        self.time_label = tk.Label(
            self.playback_frame,
            text="0:00 / 0:00",
            font=("Helvetica", 12),
            bg="#1e1e1e",
            fg="white"
        )
        self.time_label.pack(side="left", padx=20)
        
        # Segment creation controls
        segment_control_frame = tk.Frame(self, bg="#1e1e1e")
        segment_control_frame.pack(pady=15)
        
        tk.Label(
            segment_control_frame,
            text="Add Segment:",
            font=("Helvetica", 12),
            bg="#1e1e1e",
            fg="white"
        ).pack(anchor="w")
        
        # Segment input frame
        input_frame = tk.Frame(segment_control_frame, bg="#1e1e1e")
        input_frame.pack(pady=5)
        
        tk.Label(
            input_frame,
            text="Type:",
            bg="#1e1e1e",
            fg="white"
        ).pack(side="left", padx=5)
        
        self.segment_type_var = tk.StringVar(value="intro")
        self.segment_type_combo = ttk.Combobox(
            input_frame,
            textvariable=self.segment_type_var,
            values=list(self.segment_types.keys()),
            width=12,
            state="readonly"
        )
        self.segment_type_combo.pack(side="left", padx=5)
        
        tk.Label(
            input_frame,
            text="Start (MM:SS):",
            bg="#1e1e1e",
            fg="white"
        ).pack(side="left", padx=5)
        
        self.start_time_entry = tk.Entry(input_frame, width=8)
        self.start_time_entry.insert(0, "0:00")
        self.start_time_entry.pack(side="left", padx=5)
        
        tk.Label(
            input_frame,
            text="End (MM:SS):",
            bg="#1e1e1e",
            fg="white"
        ).pack(side="left", padx=5)
        
        self.end_time_entry = tk.Entry(input_frame, width=8)
        self.end_time_entry.insert(0, "0:00")
        self.end_time_entry.pack(side="left", padx=5)
        
        self.add_segment_button = tk.Button(
            input_frame,
            text="Add Segment",
            command=self.add_segment,
            bg="#4CAF50",
            fg="black",
            padx=15,
            pady=5
        )
        self.add_segment_button.pack(side="left", padx=10)
        
        # Current segments display
        segments_display_frame = tk.Frame(self, bg="#1e1e1e")
        segments_display_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        tk.Label(
            segments_display_frame,
            text="Current Segments:",
            font=("Helvetica", 12, "bold"),
            bg="#1e1e1e",
            fg="white"
        ).pack(anchor="w")
        
        # Segments listbox with scrollbar
        list_frame = tk.Frame(segments_display_frame, bg="#1e1e1e")
        list_frame.pack(fill="both", expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.segments_listbox = tk.Listbox(
            list_frame,
            bg="#2a2a2a",
            fg="white",
            selectbackground="#5ad",
            height=8,
            yscrollcommand=scrollbar.set,
            font=("Helvetica", 10)
        )
        self.segments_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.segments_listbox.yview)
        
        # Delete segment button
        self.delete_segment_button = tk.Button(
            segments_display_frame,
            text="Delete Selected Segment",
            command=self.delete_selected_segment,
            bg="#E74C3C",
            fg="black",
            padx=10,
            pady=5
        )
        self.delete_segment_button.pack(pady=5)
        
        # Navigation buttons
        nav_frame = tk.Frame(self, bg="#1e1e1e")
        nav_frame.pack(pady=20)
        
        self.prev_button = tk.Button(
            nav_frame,
            text="◀ Previous Song",
            command=self.prev_song,
            bg="#2e2e2e",
            fg="black",
            padx=20,
            pady=10,
            font=("Helvetica", 12)
        )
        self.prev_button.pack(side="left", padx=10)
        
        self.save_and_next_button = tk.Button(
            nav_frame,
            text="Save & Next Song ▶",
            command=self.save_and_next,
            bg="#3498db",
            fg="black",
            padx=20,
            pady=10,
            font=("Helvetica", 12, "bold")
        )
        self.save_and_next_button.pack(side="left", padx=10)
        
        self.finish_button = tk.Button(
            nav_frame,
            text="Finish Labeling",
            command=self.finish_labeling,
            bg="#27ae60",
            fg="black",
            padx=20,
            pady=10,
            font=("Helvetica", 12)
        )
        self.finish_button.pack(side="left", padx=10)
        
        # Update navigation buttons state
        self.update_navigation_buttons()
    
    def load_current_song(self):
        """Load the current song for labeling"""
        if not self.songs_data or self.current_song_index >= len(self.songs_data):
            return
        
        song = self.songs_data[self.current_song_index]
        song_name = song['song_name']
        song_path = Path(self.folder_path) / song_name
        
        # Update labels
        self.song_info_label.config(text=f"Current Song: {song_name}")
        
        # Calculate progress - total songs minus completed ones
        total_unlabeled = len(self.songs_data) - len(self.completed_songs)
        current_position = self.current_song_index - len([s for s in self.songs_data[:self.current_song_index] if s['song_name'] in self.completed_songs]) + 1
        self.progress_label.config(
            text=f"Song {current_position} of {total_unlabeled} unlabeled | {len(self.completed_songs)} already complete"
        )
        
        # Load audio
        try:
            self.waveform.load_audio(str(song_path))
            pygame.mixer.music.load(str(song_path))
            
            # Load existing segments if any (should be empty for unlabeled songs)
            self.current_segments = []
            self.update_segments_display()
            self.draw_timeline()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load song: {e}")
    
    def toggle_playback(self):
        """Toggle play/pause with proper position tracking"""
        if not self.is_playing:
            # Starting playback
            if self.is_paused and self.pause_position > 0:
                # Resume from paused position
                pygame.mixer.music.play(-1, start=self.pause_position)
                self.current_position = self.pause_position
            else:
                # Start from beginning or current position
                pygame.mixer.music.play(-1, start=self.current_position)
            
            self.is_playing = True
            self.is_paused = False
            self.play_button.config(text="⏸ Pause")
            self.waveform.start_playhead_at(self.current_position)
            self.update_time_display()
        else:
            # Pausing playback - save the current position
            if pygame.mixer.music.get_busy():
                # Calculate actual position in the song
                pos_ms = pygame.mixer.music.get_pos()
                if pos_ms > 0:
                    # Add the milliseconds played to where we started
                    self.pause_position = self.current_position + (pos_ms / 1000.0)
                else:
                    self.pause_position = self.current_position
            
            pygame.mixer.music.pause()
            self.is_playing = False
            self.is_paused = True
            self.play_button.config(text="▶ Play")
            self.waveform.pause_playhead()
    
    def stop_playback(self):
        """Stop playback and reset"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        self.pause_position = 0
        self.play_button.config(text="▶ Play")
        self.waveform.stop_playhead()
        self.time_label.config(text="0:00 / 0:00")
    
    def update_time_display(self):
        """Update the time display while playing"""
        if self.is_playing and pygame.mixer.music.get_busy():
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                # Calculate actual position: where we started + time played
                actual_position = self.current_position + (pos_ms / 1000.0)
                duration = self.waveform.duration
                
                # Ensure we don't exceed duration
                actual_position = min(actual_position, duration)
                
                pos_min, pos_sec = divmod(int(actual_position), 60)
                dur_min, dur_sec = divmod(int(duration), 60)
                self.time_label.config(text=f"{pos_min}:{pos_sec:02d} / {dur_min}:{dur_sec:02d}")
            self.after(100, self.update_time_display)
    
    def parse_time_string(self, time_str):
        """Parse MM:SS or M:SS format to seconds"""
        try:
            parts = time_str.strip().split(':')
            if len(parts) != 2:
                raise ValueError("Invalid time format")
            
            minutes = int(parts[0])
            seconds = float(parts[1])
            
            if seconds >= 60 or seconds < 0:
                raise ValueError("Seconds must be between 0 and 59")
            if minutes < 0:
                raise ValueError("Minutes cannot be negative")
            
            return minutes * 60 + seconds
        except:
            raise ValueError("Please use MM:SS format (e.g., 1:30)")
    
    def format_time(self, seconds):
        """Convert seconds to MM:SS format"""
        minutes, secs = divmod(int(seconds), 60)
        return f"{minutes}:{secs:02d}"
    
    def add_segment(self):
        """Add a new segment with MM:SS format support"""
        try:
            segment_type = self.segment_type_var.get()
            
            # Parse MM:SS format to seconds
            start_time = self.parse_time_string(self.start_time_entry.get())
            end_time = self.parse_time_string(self.end_time_entry.get())
            
            if start_time >= end_time:
                messagebox.showwarning("Invalid Input", "End time must be greater than start time")
                return
            
            if end_time > self.waveform.duration:
                messagebox.showwarning("Invalid Input", "End time exceeds song duration")
                return
            
            # Check for overlaps
            for seg in self.current_segments:
                if not (end_time <= seg['start'] or start_time >= seg['end']):
                    messagebox.showwarning("Overlap", "This segment overlaps with an existing segment")
                    return
            
            # Add the segment
            new_segment = {
                'type': segment_type,
                'start': start_time,
                'end': end_time
            }
            self.current_segments.append(new_segment)
            self.current_segments.sort(key=lambda x: x['start'])
            
            # Update display
            self.update_segments_display()
            self.draw_timeline()
            
            # Clear input fields and reset to 0:00
            self.start_time_entry.delete(0, tk.END)
            self.start_time_entry.insert(0, "0:00")
            self.end_time_entry.delete(0, tk.END)
            self.end_time_entry.insert(0, "0:00")
            
        except ValueError as e:
            messagebox.showwarning("Invalid Input", str(e))
    
    def delete_selected_segment(self):
        """Delete the selected segment from the list"""
        selection = self.segments_listbox.curselection()
        if selection:
            index = selection[0]
            del self.current_segments[index]
            self.update_segments_display()
            self.draw_timeline()
    
    def update_segments_display(self):
        """Update the segments listbox"""
        self.segments_listbox.delete(0, tk.END)
        for segment in self.current_segments:
            start_min, start_sec = divmod(int(segment['start']), 60)
            end_min, end_sec = divmod(int(segment['end']), 60)
            display_text = f"{segment['type']}: {start_min}:{start_sec:02d} - {end_min}:{end_sec:02d}"
            self.segments_listbox.insert(tk.END, display_text)
    
    def draw_timeline(self):
        """Draw the timeline with segments visualization"""
        self.timeline_canvas.delete("all")
        
        if self.waveform.duration == 0:
            return
        
        canvas_width = 750
        canvas_height = 30
        
        # Draw background
        self.timeline_canvas.create_rectangle(0, 0, canvas_width, canvas_height, 
                                             fill="#2a2a2a", outline="")
        
        # Draw segments
        for segment in self.current_segments:
            start_x = (segment['start'] / self.waveform.duration) * canvas_width
            end_x = (segment['end'] / self.waveform.duration) * canvas_width
            color = self.segment_types.get(segment['type'], "#95A5A6")
            
            self.timeline_canvas.create_rectangle(
                start_x, 5, end_x, 25,
                fill=color, outline="white", width=1
            )
            
            # Add label if segment is wide enough
            if end_x - start_x > 40:
                self.timeline_canvas.create_text(
                    (start_x + end_x) / 2, 15,
                    text=segment['type'],
                    fill="white",
                    font=("Helvetica", 8)
                )
    
    def save_current_segments(self):
        """Save the current segments to the JSON"""
        if not self.songs_data or self.current_song_index >= len(self.songs_data):
            return
        
        try:
            # Convert segments to the format requested (dict with tuples)
            segments_dict = {}
            for i, segment in enumerate(self.current_segments):
                # Handle multiple instances of the same type
                segment_type = segment['type']
                if segment_type in segments_dict:
                    # Add number suffix for multiple instances
                    count = 1
                    while f"{segment_type}{count}" in segments_dict:
                        count += 1
                    segment_type = f"{segment_type}{count}"
                
                segments_dict[segment_type] = [segment['start'], segment['end']]
            
            # Update the song data
            self.songs_data[self.current_song_index]['segments'] = segments_dict
            
            # Save to JSON file
            with open(self.new_json_path, 'r') as f:
                data = json.load(f)
            
            data['songs'][self.current_song_index]['segments'] = segments_dict
            
            with open(self.new_json_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Mark this song as completed
            song_name = self.songs_data[self.current_song_index]['song_name']
            self.completed_songs.add(song_name)
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save segments: {e}")
            return False
    
    def save_and_next(self):
        """Save current segments and move to next unlabeled song"""
        if self.save_current_segments():
            self.next_song()
    
    def next_song(self):
        """Move to the next unlabeled song"""
        self.stop_playback()
        self.current_song_index += 1
        self.find_next_unlabeled_song()
        self.update_navigation_buttons()
    
    def prev_song(self):
        """Move to the previous song (including already-labeled ones)"""
        if self.current_song_index > 0:
            self.stop_playback()
            self.current_song_index -= 1
            
            # Check if this song is already labeled
            song = self.songs_data[self.current_song_index]
            song_name = song['song_name']
            
            if song_name in self.completed_songs:
                response = messagebox.askyesno(
                    "Already Labeled",
                    f"'{song_name}' has already been labeled.\n\nDo you want to re-label it?"
                )
                if response:
                    # Allow re-labeling
                    self.completed_songs.discard(song_name)
                    self.load_current_song()
                else:
                    # Skip back further
                    self.prev_song()
            else:
                self.load_current_song()
            
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons"""
        self.prev_button.config(state="normal" if self.current_song_index > 0 else "disabled")
        
        # Check if we're on the last unlabeled song
        remaining_unlabeled = sum(1 for i in range(self.current_song_index + 1, len(self.songs_data)) 
                                 if self.songs_data[i]['song_name'] not in self.completed_songs)
        
        if remaining_unlabeled == 0:
            self.save_and_next_button.config(text="Save (Last Song)")
    
    def finish_labeling(self):
        """Finish the labeling process"""
        if self.current_segments:
            response = messagebox.askyesnocancel(
                "Save Current Song?",
                "Do you want to save the segments for the current song before finishing?"
            )
            if response is None:
                return
            elif response:
                self.save_current_segments()
        
        messagebox.showinfo(
            "Complete",
            f"Segment labeling complete!\nSegmented data saved to:\n{self.new_json_path}"
        )
        
        if self.on_complete:
            self.on_complete(self.new_json_path)
    
    def seek_to(self, position_seconds):
        """Seek to a specific position in the song"""
        # Stop current playback if playing
        was_playing = self.is_playing
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
        
        # Set the new position
        self.current_position = position_seconds
        self.pause_position = position_seconds
        
        # Update time display
        duration = self.waveform.duration
        pos_min, pos_sec = divmod(int(position_seconds), 60)
        dur_min, dur_sec = divmod(int(duration), 60)
        self.time_label.config(text=f"{pos_min}:{pos_sec:02d} / {dur_min}:{dur_sec:02d}")
        
        # Update waveform playhead position
        self.waveform.set_playhead_position(position_seconds)
        
        # Resume playing if it was playing before
        if was_playing:
            pygame.mixer.music.play(-1, start=position_seconds)
            self.is_playing = True
            self.is_paused = False
            self.play_button.config(text="⏸ Pause")
            self.waveform.start_playhead_at(position_seconds)
            self.update_time_display()