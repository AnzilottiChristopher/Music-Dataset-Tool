import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import pygame
from pathlib import Path
import tempfile
import shutil
import sys
from pathlib import Path

# Add the parent directory to Python path so DownBeatDetector can find DatasetTool
current_dir = Path(__file__).parent  # DownBeatTransitions folder
parent_dir = current_dir.parent  # DatasetTool folder (parent)
sys.path.insert(0, str(parent_dir))  # Add parent so DatasetTool is importable

from DownBeatDetector import BeatDrop, beatnet_detection
import numpy as np
import re


class TransitionMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DJ Transition Analyzer")
        self.root.geometry("1000x700")

        # Initialize pygame mixer for audio playback
        pygame.mixer.init()

        # Transition compatibility matrix
        self.COMPATIBLE_TRANSITIONS = {
            "outro": ["intro"],
            "cool-down": ["intro", "verse", "chorus"],
            "verse": ["chorus"],
            "build-up": ["beat-drop"],
            "chorus": ["verse", "build-up"],
        }

        # Data storage
        self.all_songs = []
        self.analyzed_songs = {}  # Cache analyzed BeatDrop objects
        self.all_transitions = []  # List of all possible transitions
        self.current_transition_idx = 0
        self.current_transition_audio = None
        self.temp_audio_file = None
        self.results_json_path = None
        self.temp_folder = None

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="DJ Transition Analyzer - Batch Mode",
            font=("Arial", 16, "bold"),
        )
        title_label.pack(pady=10)

        # Load folder section
        load_frame = ttk.LabelFrame(main_frame, text="1. Load Songs", padding="10")
        load_frame.pack(fill="x", padx=10, pady=10)

        folder_btn_frame = ttk.Frame(load_frame)
        folder_btn_frame.pack(fill="x")

        ttk.Button(
            folder_btn_frame, text="Select Song Folder", command=self.load_song_folder
        ).pack(side=tk.LEFT, padx=5)

        self.folder_status_label = ttk.Label(
            folder_btn_frame, text="No folder selected", foreground="gray"
        )
        self.folder_status_label.pack(side=tk.LEFT, padx=20)

        ttk.Button(
            folder_btn_frame, text="Analyze All Songs", command=self.analyze_all_songs
        ).pack(side=tk.LEFT, padx=5)

        self.analysis_progress = ttk.Label(load_frame, text="", foreground="blue")
        self.analysis_progress.pack(pady=5)

        # Segment filter section
        filter_frame = ttk.Frame(load_frame)
        filter_frame.pack(fill="x", pady=10)

        ttk.Label(
            filter_frame, text="Filter by segment type:", font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)

        self.segment_filter_var = tk.StringVar(value="all")
        segment_types = [
            "all",
            "intro",
            "verse",
            "chorus",
            "build-up",
            "beat-drop",
            "cool-down",
            "outro",
        ]

        self.segment_filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.segment_filter_var,
            values=segment_types,
            state="readonly",
            width=15,
        )
        self.segment_filter_combo.pack(side=tk.LEFT, padx=5)
        self.segment_filter_combo.set("all")

        ttk.Button(
            load_frame,
            text="Generate Transitions (with filter)",
            command=self.generate_all_transitions,
        ).pack(pady=10)

        # Current transition display
        transition_frame = ttk.LabelFrame(
            main_frame, text="2. Current Transition", padding="10"
        )
        transition_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Song info display
        info_frame = ttk.Frame(transition_frame)
        info_frame.pack(fill="x", pady=10)

        self.transition_info = tk.Text(info_frame, height=8, width=80, wrap=tk.WORD)
        self.transition_info.pack(side=tk.LEFT, padx=5)

        scrollbar = ttk.Scrollbar(info_frame, command=self.transition_info.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.transition_info.config(yscrollcommand=scrollbar.set)

        # Playback controls
        control_frame = ttk.Frame(transition_frame)
        control_frame.pack(pady=10)

        ttk.Button(
            control_frame,
            text="▶ Play Transition",
            command=self.play_transition,
            width=20,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame, text="⏹ Stop", command=self.stop_playback, width=15
        ).pack(side=tk.LEFT, padx=5)

        # Now Playing display
        self.now_playing_label = ttk.Label(
            transition_frame,
            text="Not playing",
            font=("Arial", 10, "italic"),
            foreground="gray",
        )
        self.now_playing_label.pack(pady=5)

        # Rating section
        rating_frame = ttk.LabelFrame(
            transition_frame, text="3. Rate & Save", padding="10"
        )
        rating_frame.pack(fill="x", pady=10)

        rate_controls = ttk.Frame(rating_frame)
        rate_controls.pack(fill="x")

        ttk.Label(
            rate_controls, text="Rating (1-10):", font=("Arial", 11, "bold")
        ).pack(side=tk.LEFT, padx=5)

        self.rating_var = tk.StringVar(value="5")
        for i in range(1, 11):
            ttk.Radiobutton(
                rate_controls, text=str(i), variable=self.rating_var, value=str(i)
            ).pack(side=tk.LEFT, padx=5)

        comment_frame = ttk.Frame(rating_frame)
        comment_frame.pack(fill="x", pady=10)

        ttk.Label(comment_frame, text="Comment (optional):").pack(side=tk.LEFT, padx=5)
        self.comment_var = tk.StringVar()
        ttk.Entry(comment_frame, textvariable=self.comment_var, width=50).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True
        )

        # Navigation buttons
        nav_frame = ttk.Frame(rating_frame)
        nav_frame.pack(pady=10)

        ttk.Button(
            nav_frame, text="← Previous", command=self.previous_transition, width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            nav_frame, text="Save & Next →", command=self.save_and_next, width=20
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            nav_frame, text="Skip (No Save) →", command=self.skip_transition, width=20
        ).pack(side=tk.LEFT, padx=5)

        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", padx=10, pady=10)

        self.progress_label = ttk.Label(
            progress_frame, text="Progress: 0/0 transitions", font=("Arial", 10)
        )
        self.progress_label.pack()

        self.progress_bar = ttk.Progressbar(
            progress_frame, length=800, mode="determinate"
        )
        self.progress_bar.pack(pady=5)

        # Status
        self.status_label = ttk.Label(
            main_frame, text="Ready to begin", foreground="green"
        )
        self.status_label.pack(pady=5)

    def normalize_segment_name(self, segment_name):
        """Remove trailing digits from segment names"""
        return re.sub(r"\d+$", "", segment_name)

    def get_segment_instance(self, segments, base_type, instance="last"):
        """Get first or last instance of a segment type"""
        matching_segments = []

        for seg_name, seg_times in segments.items():
            if self.normalize_segment_name(seg_name) == base_type:
                matching_segments.append((seg_name, seg_times))

        if not matching_segments:
            return None, None

        if instance == "first":
            return matching_segments[0]
        else:
            return matching_segments[-1]

    def find_matching_downbeat(
        self,
        exit_downbeats,
        exit_segment_times,
        entry_downbeats,
        entry_segment_times,
        proximity_threshold=0.3,
    ):
        """
        Find matching downbeats based on relative position within their segments.

        Args:
            exit_downbeats: List of downbeat times in exit segment
            exit_segment_times: [start, end] of exit segment
            entry_downbeats: List of downbeat times in entry segment
            entry_segment_times: [start, end] of entry segment
            proximity_threshold: How close to segment end (0-1, where 1 = at the end)

        Returns:
            (exit_downbeat_time, entry_downbeat_time) or (None, None)
        """
        if not exit_downbeats or not entry_downbeats:
            return None, None

        exit_start, exit_end = exit_segment_times
        entry_start, entry_end = entry_segment_times

        exit_duration = exit_end - exit_start
        entry_duration = entry_end - entry_start

        # Find exit downbeats that are close to the end of their segment
        suitable_exit_beats = []
        for beat_time in exit_downbeats:
            # Calculate relative position in segment (0 = start, 1 = end)
            relative_pos = (beat_time - exit_start) / exit_duration
            if relative_pos >= (1 - proximity_threshold):
                suitable_exit_beats.append((beat_time, relative_pos))

        if not suitable_exit_beats:
            # If no beats near end, use the last downbeat
            return exit_downbeats[-1], entry_downbeats[0]

        # Use the exit beat closest to the end
        exit_beat = sorted(suitable_exit_beats, key=lambda x: x[1], reverse=True)[0][0]
        exit_relative_pos = (exit_beat - exit_start) / exit_duration

        # Find entry downbeat with similar relative position
        best_entry_beat = None
        min_diff = float("inf")

        for beat_time in entry_downbeats:
            entry_relative_pos = (beat_time - entry_start) / entry_duration
            diff = abs(exit_relative_pos - entry_relative_pos)

            if diff < min_diff:
                min_diff = diff
                best_entry_beat = beat_time

        return exit_beat, best_entry_beat if best_entry_beat else entry_downbeats[0]

    def load_song_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Songs")
        if not folder:
            return

        # Find all audio files
        audio_files = []
        for ext in ["*.wav", "*.mp3", "*.flac"]:
            audio_files.extend(Path(folder).glob(ext))

        if not audio_files:
            messagebox.showwarning("Warning", "No audio files found in folder")
            return

        self.all_songs = sorted([str(f) for f in audio_files])
        self.folder_status_label.config(
            text=f"✓ {len(self.all_songs)} songs found", foreground="green"
        )
        self.status_label.config(
            text=f"Loaded {len(self.all_songs)} songs. Click 'Analyze All Songs'"
        )

    def analyze_all_songs(self):
        if not self.all_songs:
            messagebox.showwarning("Warning", "Load a folder first")
            return

        self.analysis_progress.config(text="Analyzing songs with BeatNet...")
        self.root.update()

        try:
            for idx, song_path in enumerate(self.all_songs):
                song_name = os.path.basename(song_path)
                self.analysis_progress.config(
                    text=f"Analyzing {idx+1}/{len(self.all_songs)}: {song_name}"
                )
                self.root.update()

                # Run BeatNet detection
                beat_times, downbeats = beatnet_detection(song_path)
                beats_time = np.array(beat_times)
                downbeat_flags = np.array(downbeats)
                downbeat_times = beats_time[downbeat_flags == 1.0]

                # Create and cache BeatDrop object
                beat_drop = BeatDrop(
                    song_path, downbeat_times, beats_time, beat_times, downbeats
                )
                self.analyzed_songs[song_path] = beat_drop

            self.analysis_progress.config(
                text=f"✓ All {len(self.all_songs)} songs analyzed!", foreground="green"
            )
            self.status_label.config(
                text="Analysis complete! Click 'Generate All Transitions'"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
            self.analysis_progress.config(text="Analysis failed", foreground="red")

    def generate_all_transitions(self):
        if not self.analyzed_songs:
            messagebox.showwarning("Warning", "Analyze songs first")
            return

        # Get selected segment filter
        segment_filter = self.segment_filter_var.get()

        # Load segment data
        try:
            with open("segmented_results.json", "r") as f:
                segment_data = json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Error", "segmented_results.json not found")
            return

        # Create segments lookup
        segments_lookup = {}
        for song in segment_data.get("songs", []):
            segments_lookup[song["song_name"]] = song.get("segments", {})

        # Generate all possible transitions
        self.all_transitions = []

        if segment_filter == "all":
            # Original behavior - use compatibility matrix
            self._generate_compatible_transitions(segments_lookup)
        else:
            # New behavior - match same segment type across all songs
            self._generate_same_segment_transitions(segments_lookup, segment_filter)

        if not self.all_transitions:
            filter_msg = (
                f" for '{segment_filter}' segments" if segment_filter != "all" else ""
            )
            messagebox.showwarning(
                "Warning", f"No compatible transitions found{filter_msg}"
            )
            return

        filter_info = (
            f" (segment type: {segment_filter})" if segment_filter != "all" else ""
        )
        messagebox.showinfo(
            "Success",
            f"Generated {len(self.all_transitions)} transitions{filter_info}!\n\n"
            "Click 'Save & Next' to begin rating.",
        )

        self.current_transition_idx = 0
        self.update_progress()
        self.load_current_transition()

    def _generate_compatible_transitions(self, segments_lookup):
        """Original method using compatibility matrix"""
        for i, song_a_path in enumerate(self.all_songs):
            for j, song_b_path in enumerate(self.all_songs):
                if i == j:
                    continue

                song_a_name = os.path.basename(song_a_path)
                song_b_name = os.path.basename(song_b_path)

                segments_a = segments_lookup.get(song_a_name, {})
                segments_b = segments_lookup.get(song_b_name, {})

                # Find compatible segment pairs
                for exit_segment_name, exit_times in segments_a.items():
                    exit_base_type = self.normalize_segment_name(exit_segment_name)

                    if exit_base_type not in self.COMPATIBLE_TRANSITIONS:
                        continue

                    # Only use LAST instance of exit segments
                    last_exit_name, last_exit_times = self.get_segment_instance(
                        segments_a, exit_base_type, "last"
                    )

                    if last_exit_name != exit_segment_name:
                        continue

                    compatible_entry_types = self.COMPATIBLE_TRANSITIONS[exit_base_type]

                    for entry_base_type in compatible_entry_types:
                        # Only use FIRST instance of entry segments
                        first_entry_name, first_entry_times = self.get_segment_instance(
                            segments_b, entry_base_type, "first"
                        )

                        if first_entry_name is None:
                            continue

                        # Get downbeats for both segments
                        beat_drop_a = self.analyzed_songs[song_a_path]
                        beat_drop_b = self.analyzed_songs[song_b_path]

                        exit_downbeats = beat_drop_a.downBeatTimesAtSegment(
                            exit_segment_name
                        )
                        entry_downbeats = beat_drop_b.downBeatTimesAtSegment(
                            first_entry_name
                        )

                        if not exit_downbeats or not entry_downbeats:
                            continue

                        # Find matching downbeats based on segment proximity
                        exit_beat, entry_beat = self.find_matching_downbeat(
                            exit_downbeats,
                            last_exit_times,
                            entry_downbeats,
                            first_entry_times,
                        )

                        if exit_beat is None or entry_beat is None:
                            continue

                        # Store transition info
                        transition = {
                            "song_a_path": song_a_path,
                            "song_b_path": song_b_path,
                            "song_a_name": song_a_name,
                            "song_b_name": song_b_name,
                            "exit_segment": exit_segment_name,
                            "entry_segment": first_entry_name,
                            "exit_time": exit_beat,
                            "entry_time": entry_beat,
                            "exit_segment_times": last_exit_times,
                            "entry_segment_times": first_entry_times,
                        }

                        self.all_transitions.append(transition)

    def _generate_same_segment_transitions(self, segments_lookup, target_segment):
        """
        Generate transitions matching the same segment type across songs.
        For example, if target_segment='chorus', find all chorus segments across
        all songs and match their downbeats based on relative position.
        """
        # First, collect all instances of the target segment across all songs
        segment_instances = []

        for song_path in self.all_songs:
            song_name = os.path.basename(song_path)
            segments = segments_lookup.get(song_name, {})
            beat_drop = self.analyzed_songs[song_path]

            # Find all segments matching the target type
            for segment_name, segment_times in segments.items():
                segment_base_type = self.normalize_segment_name(segment_name)

                if segment_base_type == target_segment:
                    downbeats = beat_drop.downBeatTimesAtSegment(segment_name)

                    if downbeats and len(downbeats) > 0:
                        segment_instances.append(
                            {
                                "song_path": song_path,
                                "song_name": song_name,
                                "segment_name": segment_name,
                                "segment_times": segment_times,
                                "downbeats": downbeats,
                                "beat_drop": beat_drop,
                            }
                        )

        if len(segment_instances) < 2:
            return  # Need at least 2 songs with this segment type

        # Now create transitions between all pairs of these segments
        for i, exit_seg in enumerate(segment_instances):
            for j, entry_seg in enumerate(segment_instances):
                # Skip if same song - cannot transition to itself
                if exit_seg["song_path"] == entry_seg["song_path"]:
                    continue

                exit_times = exit_seg["segment_times"]
                entry_times = entry_seg["segment_times"]

                # Find matching downbeats based on relative position in segment
                exit_beat, entry_beat = self.find_matching_downbeat(
                    exit_seg["downbeats"],
                    exit_times,
                    entry_seg["downbeats"],
                    entry_times,
                    proximity_threshold=0.4,  # Slightly more flexible for same-segment matching
                )

                if exit_beat is None or entry_beat is None:
                    continue

                # Store transition info
                transition = {
                    "song_a_path": exit_seg["song_path"],
                    "song_b_path": entry_seg["song_path"],
                    "song_a_name": exit_seg["song_name"],
                    "song_b_name": entry_seg["song_name"],
                    "exit_segment": exit_seg["segment_name"],
                    "entry_segment": entry_seg["segment_name"],
                    "exit_time": exit_beat,
                    "entry_time": entry_beat,
                    "exit_segment_times": exit_times,
                    "entry_segment_times": entry_times,
                }

                self.all_transitions.append(transition)

    def load_current_transition(self):
        if not self.all_transitions or self.current_transition_idx >= len(
            self.all_transitions
        ):
            self.transition_info.delete(1.0, tk.END)
            self.transition_info.insert(1.0, "No transitions available")
            self.now_playing_label.config(text="Not playing", foreground="gray")
            return

        transition = self.all_transitions[self.current_transition_idx]

        # Display transition info
        info_text = f"""
Transition {self.current_transition_idx + 1} of {len(self.all_transitions)}

EXIT SONG: {transition['song_a_name']}
  └─ Segment: {transition['exit_segment']}
  └─ Time: {transition['exit_time']:.2f}s
  └─ Segment Range: {transition['exit_segment_times'][0]:.2f}s - {transition['exit_segment_times'][1]:.2f}s

ENTRY SONG: {transition['song_b_name']}
  └─ Segment: {transition['entry_segment']}
  └─ Time: {transition['entry_time']:.2f}s
  └─ Segment Range: {transition['entry_segment_times'][0]:.2f}s - {transition['entry_segment_times'][1]:.2f}s

Transition: {transition['exit_segment']} → {transition['entry_segment']}
"""

        self.transition_info.delete(1.0, tk.END)
        self.transition_info.insert(1.0, info_text)

        # Reset now playing label
        self.now_playing_label.config(text="Ready to play", foreground="gray")

        # Generate audio file
        self.generate_transition_audio(transition)
        self.update_progress()

    def generate_transition_audio(self, transition):
        try:
            from TransitionHelper import compute_transition_audio

            # Unload any currently playing audio and clean up temp file
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()

            if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                try:
                    os.remove(self.temp_audio_file)
                except PermissionError:
                    pass  # File still locked, will create new one with different name

            self.temp_audio_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".wav"
            ).name

            self.status_label.config(
                text="Generating transition audio...", foreground="blue"
            )
            self.root.update()

            compute_transition_audio(
                song_a=transition["song_a_path"],
                song_b=transition["song_b_path"],
                time_a=transition["exit_time"],
                time_b=transition["entry_time"],
                crossfade_duration=0.0,  # Immediate cut
                output_path=self.temp_audio_file,
            )

            self.current_transition_audio = self.temp_audio_file
            self.status_label.config(
                text="✓ Ready to play! Press '▶ Play Transition'", foreground="green"
            )

        except Exception as e:
            self.status_label.config(text="Failed to generate audio", foreground="red")
            messagebox.showerror("Error", f"Failed to generate: {str(e)}")

    def play_transition(self):
        if not self.current_transition_audio or not os.path.exists(
            self.current_transition_audio
        ):
            messagebox.showwarning("Warning", "No transition audio available")
            return

        if not self.all_transitions or self.current_transition_idx >= len(
            self.all_transitions
        ):
            return

        try:
            transition = self.all_transitions[self.current_transition_idx]

            pygame.mixer.music.load(self.current_transition_audio)
            pygame.mixer.music.play()

            # Update now playing display
            now_playing_text = f"♪ Now Playing: {transition['song_a_name']} → {transition['song_b_name']}"
            self.now_playing_label.config(text=now_playing_text, foreground="blue")
            self.status_label.config(text="♪ Playing transition...", foreground="blue")
        except Exception as e:
            messagebox.showerror("Error", f"Playback failed: {str(e)}")

    def stop_playback(self):
        pygame.mixer.music.stop()
        self.now_playing_label.config(text="Playback stopped", foreground="gray")
        self.status_label.config(text="Playback stopped", foreground="gray")

    def save_and_next(self):
        if not self.all_transitions:
            return

        # Stop playback and unload audio before saving
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

        # Initialize results file if needed
        if not self.results_json_path:
            self.results_json_path = "transition-results.json"
            with open(self.results_json_path, "w") as f:
                json.dump({"transitions": []}, f, indent=2)

        transition = self.all_transitions[self.current_transition_idx]

        # Create rating record
        rating_record = {
            "song_a": transition["song_a_name"],
            "song_b": transition["song_b_name"],
            "exit_segment": transition["exit_segment"],
            "entry_segment": transition["entry_segment"],
            "rating": int(self.rating_var.get()),
            "comment": self.comment_var.get(),
        }

        # Append to file
        with open(self.results_json_path, "r") as f:
            data = json.load(f)

        data["transitions"].append(rating_record)

        with open(self.results_json_path, "w") as f:
            json.dump(data, f, indent=2)

        # Reset comment for next transition
        self.comment_var.set("")

        # Move to next
        self.current_transition_idx += 1

        if self.current_transition_idx >= len(self.all_transitions):
            messagebox.showinfo(
                "Complete!",
                f"All {len(self.all_transitions)} transitions rated!\n\n"
                f"Results saved to: {self.results_json_path}",
            )
            self.status_label.config(
                text="✓ All transitions complete!", foreground="green"
            )
        else:
            self.load_current_transition()

    def skip_transition(self):
        """Skip to next without saving"""
        # Stop and unload audio
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

        self.current_transition_idx += 1
        self.comment_var.set("")

        if self.current_transition_idx >= len(self.all_transitions):
            messagebox.showinfo("Complete!", "Reached end of transitions")
            self.status_label.config(text="End of transitions", foreground="gray")
        else:
            self.load_current_transition()

    def previous_transition(self):
        """Go back to previous transition"""
        # Stop and unload audio
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

        if self.current_transition_idx > 0:
            self.current_transition_idx -= 1
            self.comment_var.set("")
            self.load_current_transition()

    def update_progress(self):
        if not self.all_transitions:
            return

        progress_text = f"Progress: {self.current_transition_idx + 1}/{len(self.all_transitions)} transitions"
        self.progress_label.config(text=progress_text)

        progress_percent = (
            (self.current_transition_idx + 1) / len(self.all_transitions)
        ) * 100
        self.progress_bar["value"] = progress_percent


if __name__ == "__main__":
    root = tk.Tk()
    app = TransitionMergerGUI(root)
    root.mainloop()
