import json
import librosa
import numpy as np
import os, sys
from pathlib import Path
import soundfile as sf


"""
This file will contain all of the helper files to do the following
- take the current json file and copy it so we do not overrwite what we had originally
- get song name A and song name B, and get their phrase boundaries respectively
- for each phrase boundary i in song A and phrase boundary j in song B, make a simple cross fade transition
- one by one, load each, allow us to play, and rank, then update the NEW json file with this information
- Once done, remove the audio files it just created, now swap song A and B (to compute them the other way)
- Once this is done, revert back to the original song A, now go to Song C, and so on.

- one that loop is done (so one song has been ranked with all other songs) advanced the loop forward and continue
until we have ranked all song pairs in both directions
"""

# so, we take 'results.json', make a new copy and rename it "results-analyzed.json"
# should also return that path so that we can add to it when we rank transitions
def create_json_copy(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    # we should rightfulyl assume json_path is absolute
    old_path = Path(json_path)
    new_path = old_path.with_name("transition-results.json")
    
    with open(new_path,'w') as f:
        json.dump(data, f, indent=4)
        
    return new_path
    

# I am not sure as to what is the best way to save these files exactly (or where to save them to)
# but they can be removed afterwards
# def compute_transition_audio(song_a=None, song_b=None, phrase_boundaries_=None, phrase_boundaries_b=None):
#     pass

def compute_transition_audio(
    song_a=None, 
    song_b=None, 
    time_a=None, 
    time_b=None,
    crossfade_duration=3.0,
    pre_transition_duration=5.0,
    post_transition_duration=5.0,
    output_path="crossfade_output.wav",
    sr=None
):
 
    
    # Load audio files if paths are provided
    if isinstance(song_a, str):
        audio_a, sr_a = librosa.load(song_a, sr=sr, mono=False)
    else:
        audio_a = song_a
        sr_a = sr if sr is not None else 22050
    
    if isinstance(song_b, str):
        audio_b, sr_b = librosa.load(song_b, sr=sr_a, mono=False)
    else:
        audio_b = song_b
        sr_b = sr_a
    
    # Use the sample rate from song_a if not specified
    if sr is None:
        sr = sr_a
    
    # Ensure both audio files have the same sample rate
    if sr_a != sr_b:
        audio_b = librosa.resample(audio_b, orig_sr=sr_b, target_sr=sr_a)
        sr_b = sr_a
    
    # Handle stereo/mono compatibility
    if audio_a.ndim == 1 and audio_b.ndim == 2:
        audio_a = np.stack([audio_a, audio_a])
    elif audio_a.ndim == 2 and audio_b.ndim == 1:
        audio_b = np.stack([audio_b, audio_b])
    
    # Convert time positions to sample indices
    start_a_samples = int(time_a * sr)
    start_b_samples = int(time_b * sr)
    
    # Calculate segment durations in samples
    pre_samples = int(pre_transition_duration * sr)
    crossfade_samples = int(crossfade_duration * sr)
    post_samples = int(post_transition_duration * sr)
    
    # Handle edge case where time_a is at or near the beginning
    # We need to ensure we have enough audio for the crossfade
    if start_a_samples < pre_samples:
        # Adjust pre_samples to what's actually available
        actual_pre_samples = start_a_samples
    else:
        actual_pre_samples = pre_samples
    
    # Extract the segments from each song
    # Segment from song A: starts before the crossfade point
    segment_a_start = max(0, start_a_samples - actual_pre_samples)
    segment_a_end = min(audio_a.shape[-1], start_a_samples + crossfade_samples)
    
    # Ensure we have enough audio from song A for the crossfade
    available_a_for_crossfade = segment_a_end - start_a_samples
    if available_a_for_crossfade < crossfade_samples:
        print(f"Warning: Song A has only {available_a_for_crossfade/sr:.2f}s available for crossfade, adjusting crossfade duration")
        actual_crossfade_samples = available_a_for_crossfade
    else:
        actual_crossfade_samples = crossfade_samples
    
    # Segment from song B: starts at the crossfade point
    segment_b_start = start_b_samples
    segment_b_end = min(audio_b.shape[-1], start_b_samples + actual_crossfade_samples + post_samples)
    
    # Check if song B has enough audio for the crossfade
    available_b_for_crossfade = min(audio_b.shape[-1] - segment_b_start, actual_crossfade_samples)
    if available_b_for_crossfade < actual_crossfade_samples:
        print(f"Warning: Song B has only {available_b_for_crossfade/sr:.2f}s available for crossfade, adjusting")
        actual_crossfade_samples = available_b_for_crossfade
    
    # Extract segments
    if audio_a.ndim == 1:
        segment_a = audio_a[segment_a_start:segment_a_end]
        segment_b = audio_b[segment_b_start:segment_b_end]
    else:
        segment_a = audio_a[:, segment_a_start:segment_a_end]
        segment_b = audio_b[:, segment_b_start:segment_b_end]
    
    # Recalculate actual samples based on what we extracted
    actual_pre_samples = start_a_samples - segment_a_start
    actual_crossfade_samples = min(
        actual_crossfade_samples,
        segment_a.shape[-1] - actual_pre_samples,
        segment_b.shape[-1] - (segment_b_start - segment_b_start)  # Available in segment_b
    )
    actual_post_samples = segment_b.shape[-1] - actual_crossfade_samples
    
    # Create the crossfade
    # Pre-transition part (only song A)
    if audio_a.ndim == 1:
        pre_transition = segment_a[:actual_pre_samples]
    else:
        pre_transition = segment_a[:, :actual_pre_samples]
    
    # Crossfade part
    if actual_crossfade_samples > 0:
        # Create fade out and fade in curves
        fade_out = np.linspace(1, 0, actual_crossfade_samples)
        fade_in = np.linspace(0, 1, actual_crossfade_samples)
        
        if audio_a.ndim == 1:
            crossfade_a = segment_a[actual_pre_samples:actual_pre_samples + actual_crossfade_samples]
            crossfade_b = segment_b[:actual_crossfade_samples]
            
            # Apply fades
            crossfade_a_faded = crossfade_a * fade_out
            crossfade_b_faded = crossfade_b * fade_in
            
            # Mix the crossfaded parts
            crossfade_mixed = crossfade_a_faded + crossfade_b_faded
        else:
            crossfade_a = segment_a[:, actual_pre_samples:actual_pre_samples + actual_crossfade_samples]
            crossfade_b = segment_b[:, :actual_crossfade_samples]
            
            # Apply fades
            crossfade_a_faded = crossfade_a * fade_out[np.newaxis, :]
            crossfade_b_faded = crossfade_b * fade_in[np.newaxis, :]
            
            # Mix the crossfaded parts
            crossfade_mixed = crossfade_a_faded + crossfade_b_faded
    else:
        crossfade_mixed = np.array([])
    
    # Post-transition part (only song B)
    if audio_b.ndim == 1:
        post_transition = segment_b[actual_crossfade_samples:actual_crossfade_samples + actual_post_samples]
    else:
        post_transition = segment_b[:, actual_crossfade_samples:actual_crossfade_samples + actual_post_samples]
    
    # Combine all parts
    if audio_a.ndim == 1:
        combined_audio = np.concatenate([
            pre_transition,
            crossfade_mixed,
            post_transition
        ])
    else:
        combined_audio = np.concatenate([
            pre_transition,
            crossfade_mixed,
            post_transition
        ], axis=1)
    
    # Normalize to prevent clipping
    max_val = np.abs(combined_audio).max()
    if max_val > 1.0:
        combined_audio = combined_audio / max_val * 0.95
    
    # Save the output
    if audio_a.ndim == 2:
        # Transpose for soundfile (expects shape: (samples, channels))
        combined_audio = combined_audio.T
    
    sf.write(output_path, combined_audio, sr)
    print(f"Crossfade audio saved to: {output_path}")
    
    return combined_audio, sr


if __name__ == "__main__":
    # new_path = create_json_copy("/Users/alexpower/Documents/Music-Dataset-Tool/results.json")
    # print(new_path)
    song_a = '/Users/alexpower/Documents/Music-Dataset-Tool/Music/wav_files/waitingforlove-avicii.wav'
    song_b = '/Users/alexpower/Documents/Music-Dataset-Tool/Music/wav_files/wakemeup-avicii.wav'
    
    new_mix = compute_transition_audio(song_a, song_b, time_a=215.0, time_b=0.0)