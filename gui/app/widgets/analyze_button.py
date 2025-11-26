import tkinter as tk
from app.widgets.helper_scripts.create_transition_audio import compute_transition_audio
from tkinter import messagebox
import os
import json
from pathlib import Path
import shutil
import librosa
import numpy as np

import matplotlib

matplotlib.use("Agg")  # noqa: E402
import matplotlib.pyplot as plt

from jupyter_core.version import parts


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
            pady=5,
        )

        self.analyze_button.pack(pady=10)
        
        self.COMPATIBLE_TRANSITIONS = {
            "outro": ["intro"],
            "cool-down": ["intro", "verse", "chorus"],
            "verse": ["chorus"],
            "build-up": ["beat-drop"], 
            "chorus": ["verse", "build-up"],
        }

    # so now, we loop through the json, get boths songs, and load them.
    # then for each phrase boundary compute the transition clips
    # so if there are n^2 phrase boundaries, then we have n^2 to rank for each song
    # so each song pair generates 2*(n^2) rankings, then move on down the list changing song a
    def analyze_pressed(self):
        with open(self.json_path, "r") as f:
            data = json.load(f)

        original_folder_path = Path(self.folder_path)
        new_folder_name = "transition_files"
        new_folder_path = original_folder_path.parent / new_folder_name
        
        print(f"new folder path name: {new_folder_path}")

        if new_folder_path.exists():
            shutil.rmtree(new_folder_path)

        new_folder_path.mkdir(parents=True)

        messagebox.showinfo(
            title="Analysis will now begin.",
            message="Depending on the length of songs, this may take a while",
        )

        song_array = data["songs"]
        for i, song_a in enumerate(song_array):
            for j, song_b in enumerate(song_array):
                # Skip matching songs with each other and ones already computed
                if i <= j:
                    continue

                # Get segments for both songs
                segments_a = song_a.get("segments", {})
                segments_b = song_b.get("segments", {})

                # Create transitions from A to B
                self._create_segment_transitions(
                    song_a, song_b, segments_a, segments_b, new_folder_path
                )

<<<<<<< HEAD
                        exit_time = self._time_to_secs(exit_boundary)
                        entry_time = self._time_to_secs(entry_boundary)

                        song_a_path = os.path.join(
                            self.folder_path, song_a["song_name"]
                        )
                        song_b_path = os.path.join(
                            self.folder_path, song_b["song_name"]
                        )

                        audio_file_name = f"{
                            song_a['song_name']}-TO-{song_b['song_name']}-exit{exit_time}-entry{entry_time}.wav"

                        output_path = new_folder_path / audio_file_name

                        exit_time = self._time_to_secs(exit_boundary)
                        entry_time = self._time_to_secs(entry_boundary)

                        # trend_a = compute_trend_line(
                        #     song_a_path,
                        #     boundary_time=exit_time,
                        #     duration=2.0,
                        #     visualize=False,
                        #     save_dir="debug_trends",
                        # )
                        # trend_b = compute_trend_line(
                        #     song_b_path,
                        #     boundary_time=entry_time + 2.0,
                        #     duration=2.0,
                        #     visualize=False,
                        #     save_dir="debug_trends",
                        # )

                        # end_loud_a = np.mean(trend_a[-50:])
                        # start_loud_b = np.mean(trend_b[:50])

                        # if abs(end_loud_a - start_loud_b) < 0.1:
                        #     _ = compute_transition_audio(
                        #         song_a=song_a_path,
                        #         song_b=song_b_path,
                        #         time_a=exit_time,
                        #         time_b=entry_time,
                        #         output_path=output_path,
                        #     )
                        # else:
                        #     print("Skipping transition")

                        # Uncomment this and comment out from exit_time to print for the original way
                        _ = compute_transition_audio(
                            song_a=song_a_path,
                            song_b=song_b_path,
                            time_a=exit_time,
                            time_b=entry_time,
                            output_path=output_path,
                        )

                # NOW WE GO THE OTHER WAY, ESSENTIALLY COPYING WHAT WE HAVE DONE HERE
                exit_boundaries_b = song_b["features"]["last_phrase_boundaries"]
                entry_boundaries_a = song_a["features"]["first_phrase_boundaries"]

                for exit_boundary in exit_boundaries_b:
                    for entry_boundary in entry_boundaries_a:

                        exit_time = self._time_to_secs(exit_boundary)
                        entry_time = self._time_to_secs(entry_boundary)

                        song_a_path = os.path.join(
                            self.folder_path, song_b["song_name"]
                        )
                        song_b_path = os.path.join(
                            self.folder_path, song_a["song_name"]
                        )

                        audio_file_name = f"{
                            song_b['song_name']}-TO-{song_a['song_name']}-exit{exit_time}-entry{entry_time}.wav"

                        output_path = new_folder_path / audio_file_name

                        exit_time = self._time_to_secs(exit_boundary)
                        entry_time = self._time_to_secs(entry_boundary)

                        # trend_a = compute_trend_line(
                        #     song_a_path,
                        #     boundary_time=exit_time,
                        #     duration=2.0,
                        #     visualize=False,
                        #     save_dir="debug_trends",
                        # )
                        # trend_b = compute_trend_line(
                        #     song_b_path,
                        #     boundary_time=entry_time + 2.0,
                        #     duration=2.0,
                        #     visualize=False,
                        #     save_dir="debug_trends",
                        # )

                        # end_loud_a = np.mean(trend_a[-50:])
                        # start_loud_b = np.mean(trend_b[:50])

                        # if abs(end_loud_a - start_loud_b) < 0.1:
                        #     _ = compute_transition_audio(
                        #         song_a=song_a_path,
                        #         song_b=song_b_path,
                        #         time_a=exit_time,
                        #         time_b=entry_time,
                        #         output_path=output_path,
                        #     )
                        # else:
                        #     print("Skipping transition")

                        # Uncomment this and comment out from exit_time to print for the original way
                        _ = compute_transition_audio(
                            song_a=song_a_path,
                            song_b=song_b_path,
                            time_a=exit_time,
                            time_b=entry_time,
                            output_path=output_path,
                        )
=======
                # Create transitions from B to A
                self._create_segment_transitions(
                    song_b, song_a, segments_b, segments_a, new_folder_path
                )
>>>>>>> 71599239f067195c618ab9286c86f83123679816

        if callable(self.on_complete):
            self.on_complete(new_folder_path)
    
    def _normalize_segment_name(self, segment_name):
        import re
        # match any trailing digits and remove them
        return re.sub(r'\d+$', '', segment_name)
    
    def _get_segment_instance(self, segments, base_type, instance='last'):
        """Get first or last instance of a segment type.
        
        Args:
            segments: Dict of all segments
            base_type: Base segment name (e.g., 'chorus')
            instance: 'first' or 'last'
        
        Returns:
            (segment_name, segment_times) or (None, None)
        """
        matching_segments = []
        
        for seg_name, seg_times in segments.items():
            if self._normalize_segment_name(seg_name) == base_type:
                matching_segments.append((seg_name, seg_times))
        
        if not matching_segments:
            return None, None
        
        if instance == 'first':
            return matching_segments[0]
        else:  # 'last'
            return matching_segments[-1]
    
    def _create_segment_transitions(self, song_a, song_b, segments_a, segments_b, output_folder):
        song_a_path = os.path.join(self.folder_path, song_a["song_name"])
        song_b_path = os.path.join(self.folder_path, song_b["song_name"])
        
        # Iterate through exit segments of song A
        for exit_segment_type, exit_times in segments_a.items():
            exit_base_type = self._normalize_segment_name(exit_segment_type)
            
            if exit_base_type not in self.COMPATIBLE_TRANSITIONS:
                continue
                
            compatible_entry_types = self.COMPATIBLE_TRANSITIONS[exit_base_type]
            
            # Get the end time of the exit segment
            if isinstance(exit_times, list) and len(exit_times) >= 2:
                exit_time = exit_times[1]
            else:
                continue
            
            # Only use LAST instance of exit segments
            last_exit_name, last_exit_times = self._get_segment_instance(segments_a, exit_base_type, 'last')
            if last_exit_name != exit_segment_type:
                continue  # Skip if this isn't the last instance
            
            # Find compatible entry segments in song B
            for entry_base_type in compatible_entry_types:
                # Only use FIRST instance of entry segments
                first_entry_name, first_entry_times = self._get_segment_instance(segments_b, entry_base_type, 'first')
                
                if first_entry_name is None:
                    continue
                
                if isinstance(first_entry_times, list) and len(first_entry_times) >= 1:
                    entry_time = first_entry_times[0]
                else:
                    continue
                
                # Determine transition style based on segment pair
                transition_style = self._get_transition_style(exit_base_type, entry_base_type)
                
                audio_file_name = f"{song_a['song_name']}-TO-{song_b['song_name']}-{exit_segment_type}-to-{first_entry_name}.wav"
                output_path = output_folder / audio_file_name

                _ = compute_transition_audio(
                    song_a=song_a_path,
                    song_b=song_b_path,
                    time_a=exit_time,
                    time_b=entry_time,
                    output_path=output_path,
                    **transition_style  # Unpack the style parameters
                )
                    
    def _time_to_secs(self, time):
        str_representation = str(time)
        part = str_representation.split(":")

        if len(part) == 2:
            minutes, seconds = part
            return int(minutes) * 60 + float(seconds)
        else:
            return float(part[0])

        # minutes = minutes[1]
        #
        # return float((int(minutes) * 60) + (int(seconds)))
        
    def _get_transition_style(self, exit_type, entry_type):
        """Return transition parameters based on segment types."""
        
        # The "money" transition - build-up to beat-drop
        if exit_type == "build-up" and entry_type == "beat-drop":
            return {
                'crossfade_duration': 0.3,  # Very short, almost a cut
                'pre_transition_duration': 4.0,
                'post_transition_duration': 4.0
            }
        
        # High energy transitions
        if exit_type in ["beat-drop", "chorus"] and entry_type in ["verse", "cool-down"]:
            return {
                'crossfade_duration': 2.5,  # Longer to smooth the energy drop
                'pre_transition_duration': 5.0,
                'post_transition_duration': 5.0
            }
        
        # Clean song-to-song transitions
        if exit_type in ["outro", "cool-down"] and entry_type in ["intro", "verse"]:
            return {
                'crossfade_duration': 2.0,  # Standard crossfade
                'pre_transition_duration': 5.0,
                'post_transition_duration': 5.0
            }
        
        # Verse to chorus (common, keep it tight)
        if exit_type == "verse" and entry_type == "chorus":
            return {
                'crossfade_duration': 1.0,  # Quick transition
                'pre_transition_duration': 4.0,
                'post_transition_duration': 6.0
            }
        
        # Default for everything else
        return {
            'crossfade_duration': 1.0,
            'pre_transition_duration': 5,
            'post_transition_duration': 5
        }


def compute_trend_line(
    song, boundary_time, duration=2.0, num_windows=700, visualize=False, save_dir=None
    ):
    y, sr = librosa.load(song, sr=None)

    start_sample = max(0, int((boundary_time - duration) * sr))
    end_sample = min(len(y), int(boundary_time * sr))

    segment = y[start_sample:end_sample]

    if len(segment) < num_windows:
        segment = np.pad(segment, (0, num_windows - len(segment)))

    total_samples = len(segment)
    window_size = total_samples // num_windows
    trimmed = segment[: window_size * num_windows].reshape(num_windows, window_size)

    trend_line = np.mean(np.abs(trimmed), axis=1)
    trend_line /= trend_line.max() + 1e-9

    if visualize and save_dir:
        os.makedirs(save_dir, exist_ok=True)
        fig, ax = plt.subplots(figsize=(10, 4))
        times = np.linspace(0, duration, len(segment))
        trend_times = np.linspace(0, duration, len(trend_line))
        ax.plot(times, segment, alpha=0.6, color="gray", label="Waveform")
        ax.plot(
            trend_times,
            trend_line * np.max(np.abs(segment)),
            color="red",
            linewidth=2,
            label="Trend Line",
        )
        ax.set_title(f"Trend Line at {boundary_time:.2f}s")
        ax.set_xlabel("Time (s)")
        ax.legend()
        plt.tight_layout()
        fig.savefig(os.path.join(save_dir, f"trend_{boundary_time:.2f}.png"))
        plt.close(fig)

    return trend_line
