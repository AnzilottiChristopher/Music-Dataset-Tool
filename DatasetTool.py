import os
from locale import normalize
from pathlib import Path
from scipy.signal import butter, filtfilt
from sklearn.metrics.pairwise import cosine_similarity

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

    #Features
    chroma = compute_chroma(y, sr)
    mfcc = compute_mfcc(y, sr)
    tempogram, onset_env = compute_tempogram(y, sr)
    features = np.concatenate([chroma, mfcc, tempogram, onset_env], axis=0)

    # Part comes from Chatgpt because
    # I couldn't fully understand how to
    # recreate Foote's design https://ccrma.stanford.edu/workshops/mir2009/references/Foote_00.pdf
    SSM[i, j] = cosine_similarity(features.T)
    novelty = compute_novelty(SSM, sr)
    # phrase_boundaries = post_process_novelty()

def post_process_novelty(novelty, sr, hop_length = 512, L=None, smoothing_window=5, min_peak_distance_sec=1.0,
                         threshold_factor=1.0):
    n_frames = len(novelty)



def compute_novelty(SSM, sr, L=None, hop_length=512):
    n_frames = SSM.shape[0]
    novelty = np.zeros(n_frames)
    if L is None:
        L = int(0.5 * sr / hop_length)

    for t in range(L, n_frames - L):
        left_block = SSM[t-L:t, t-l:t]
        right_block = SSM[t:t+L, t:t+L]

        novelty[t] = np.sum(np.abs(left_block - right_block))
    return novelty


# Detects the beat/tempo structure
# The background beat that is played
# Also detects onset which is when the musical note begins
def compute_tempogram(y, sr):
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr)
    tempogram = librosa.util.normalize(tempogram)
    onset_env = librosa.util.normalize(onset_env)
    return tempogram, onset_env

# Computes the timbre (texture or tone color)
# The unique sounds of the instruments
# Helps detect sudden changes in instruments or vocals
def compute_mfcc(y, sr):
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    timbre = librosa.feature.delta(mfcc)
    mfcc_features = np.concatenate((mfcc, timbre))
    librosa.util.normalize(mfcc_features, axis=1)
    return mfcc_features


# Extracts the Chroma which is the quality of pitch
# Used to be categorized into one of twelve distinct pitch classes
def compute_chroma(y, sr):
    S = np.abs(librosa.stft(y))
    chroma = librosa.feature.chroma_stft(S, sr=sr)
    chroma = librosa.decompose.nn_filter(chroma)
    chroma = librosa.util.normalize(chroma, azis=0)
    return chroma


def preprocessing(songs):
    song = songs[0]
    y, sr = librosa.load(song['path'])
    y = librosa.util.normalize(y)
    y = highpass_filter(y, sr)

    return y, sr


def highpass_filter(y, sr, cutoff=100.0):
    b, a = butter(N=2,  Wn=cutoff / (sr / 2.0), btype='high', analog=False)
    y = filtfilt(b, a, y)
    return y



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


