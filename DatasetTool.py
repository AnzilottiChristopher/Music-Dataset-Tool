import os
from locale import normalize
from pathlib import Path
from scipy.signal import butter, filtfilt

import librosa
import numpy as np

class SongLoader:
    def __init__(self):
        self.songs = []

    def load_songs(self, file_path, sr=None):

        if isinstance(file_path, str):
            filePath = Path(file_path)

        # Taking each file in filepath
        # for file in filePath:
        #     try:
        #         y, sr = librosa.load(file, sr=sr) # loads the raw waveform in y and stores the sample rate in sr
        #         self.songs.append({'path': file, 'y': y, 'sr': sr})
        #     except Exception as e:
        #         print(f" could not load {file}: {e}")
        try:
            y, sr = librosa.load(filePath, sr=sr)
            self.songs.append({'path': filePath, 'y': y, 'sr': sr})
        except Exception as e:
            print(f" could not load {file_path}: {e}")

    def get_songs(self):
        return self.songs

def get_phrase_boundaries_complex(songs):
    y, sr = preprocessing(songs)
    pass


def preprocessing(songs):
    song = songs[0]
    y, sr = librosa.load(song['path'])
    y = librosa.util.normalize(y)
    y = highpass_filter(y, sr)

    return y, sr


def highpass_filter(y, sr, cutoff=100.0):
    b, a = butter(N=2,  Wn=cutoff / (sr / 2.0), btype='high', analog=False)
    y = filtfilt(b, a, y)




def simple_get_phrase_boundaries(songs):
    #!Implementation of single song

    song = songs[0]
    y = song['y']
    sr = song['sr']
    y = y[:sr*30] #first 30 seconds


    #Approximate Frames of note onsets
    #onset_env = librosa.onset.onset_strength(y = song['y'], sr = song['sr'], units = 'frames')

    rms = librosa.feature.rms(y=y)[0]

    #Chroma feature
    #Look for large sudden changes in chord or key
    chroma = librosa.feature.chroma_stft(y = y, sr = sr)
    chroma_diff = np.sum(np.abs(np.diff(chroma, axis=1)), axis=0)

    rms_threshold = 0.05
    candidate_frames = np.where((rms[:-1] < rms_threshold) & (chroma_diff > chroma_diff.mean()))[0]

    #Conversion from frames to sec
    boundaries_sec = librosa.frames_to_time(candidate_frames, sr=sr)

    print("likely boundaries (seconds):")
    for t in boundaries_sec:
        print(f"{t:.2f}s")


if __name__ == "__main__":
    #Current implementation will print a VERY SIMPLE implementation of finding phrase boundaries
    #Need to adjust to a new method
    #But will load a song and find the phrase boundaries in the first 30 seconds (doesn't do well)
    loader = SongLoader()
    loader.load_songs("Music/Clarity.wav")

    songs = loader.get_songs()
    if songs:
        simple_get_phrase_boundaries(songs)
    else:
        print("no songs")


