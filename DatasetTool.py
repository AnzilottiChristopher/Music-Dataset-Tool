import glob
import os
import librosa
import numpy as np
import re
import json

from locale import normalize
from pathlib import Path
from scipy.signal import butter, filtfilt, find_peaks
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import pearsonr
from multiprocessing import Pool, Lock, Manager
from multiprocessing.dummy import Pool as ThreadPool
from WriteToJson import writeToJson


class SongLoader:
    def __init__(self):
        self.songs = []

    def load_songs(self, file_path, sr=None):

        if isinstance(file_path, str):
            filePath = Path(file_path)

        # Taking each file in filepath
        if isinstance(file_path, (list, tuple)):
            for file in file_path:
                try:
                    y, sr = librosa.load(file, sr=sr) # loads the raw waveform in y and stores the sample rate in sr
                    self.songs.append({'path': file, 'y': y, 'sr': sr})
                except Exception as e:
                    print(f" could not load {file}: {e}")
        else:
            try:
                y, sr = librosa.load(filePath, sr=sr)
                self.songs.append({'path': filePath, 'y': y, 'sr': sr})
            except Exception as e:
                print(f" could not load {file_path}: {e}")

    def get_songs(self):
        return self.songs





def get_phrase_boundaries_complex(song, lock):
    y_harm, y_perc, sr = preprocessing(song)

    #Harmonic Features
    chroma = compute_chroma(y_harm, sr)
    mfcc = compute_mfcc(y_harm, sr)

    #Percussion Features
    tempogram, onset_env = compute_tempogram(y_perc, sr)
    flux = compute_spectral_flux(y_perc, sr)
    flux = np.pad(flux, (0, chroma.shape[1] - flux.shape[0]), mode='constant')

    features = np.concatenate([chroma, mfcc, tempogram, onset_env[np.newaxis, :], flux[np.newaxis, :]], axis=0)
    features = librosa.util.normalize(features)

    # Part comes from Chatgpt because
    # I couldn't fully understand how to
    # recreate Foote's design https://ccrma.stanford.edu/workshops/mir2009/references/Foote_00.pdf
    SSM = cosine_similarity(features.T)
    # novelty = compute_novelty(SSM, sr)
    novelty = compute_novelty_gaussian(SSM, sr)
    phrase_boundaries = post_process_novelty(novelty, sr)

    path = Path(song['path']).as_posix()

    results_path = "PhraseBoundaries_Results.json"

    data_dump = [
        {
            "Song_name": re.sub(r'^Music/wav_files/|\.wav$', '', path + ':'),
            "features": {
                "bpm": "",
                "key": "",
                "scale": "",
                "key_strength": "",
                "first_phrase_boundaries": format_boundaries(phrase_boundaries[:25]),
                "last_phrase_boundaries": format_boundaries(phrase_boundaries[len(phrase_boundaries) - 25:]),
            }
        }
    ]

    file_json = writeToJson(data_dump, results_path)
    with lock:
        if not os.path.exists(results_path):
            file_json.create_file()
        else:
            file_json.add_entry(data_dump)



# Converts to minute:second format
def format_boundaries(phrase_boundaries):
    formatted = []
    for t in phrase_boundaries:
        minutes = int(t // 60)
        seconds = t % 60
        formatted.append(f"{minutes:02d}:{seconds:04.1f}")
    return formatted

#  Takes the novelty function and converts it into phrase boundary times
#  Only considers novelty value above certain maxima that meets the criteria
def post_process_novelty(novelty, sr, hop_length = 512, L=None, smoothing_window=25, min_peak_distance_sec=1.0,
                         threshold_factor=1):
    n_frames = len(novelty)
    if L is None:
        L = int(2.0 * sr / hop_length)

    novelty_smooth = np.convolve(novelty, np.ones(smoothing_window)/smoothing_window, mode='same')

    min_height = np.mean(novelty_smooth) * threshold_factor
    min_distance_frames = int(min_peak_distance_sec * sr / hop_length)

    peaks, _ = find_peaks(novelty_smooth, height=min_height, distance=min_distance_frames)

    # if len(peaks) == 0:
    #     peaks = np.arange(L, n_frames, 2*L)

    valid_peaks = []
    min_sustain_frames = int(0.2 * sr / hop_length)

    for peak in peaks:
        start = max(0, peak - min_sustain_frames // 2)
        end = min(n_frames, peak + min_sustain_frames // 2)
        region = novelty_smooth[start:end]
        if np.mean(region > min_height) > 0.6:
            valid_peaks.append(peak)
    if len(valid_peaks) == 0:
        valid_peaks = np.arange(L, n_frames, 2*L)

    return librosa.frames_to_time(valid_peaks, sr=sr, hop_length=hop_length)
    # return librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)

def compute_novelty_gaussian(SSM, sr, L=None, hop_length=512, sigma=1.0):
    n_frames = SSM.shape[0]
    novelty = np.zeros(n_frames)

    if L is None:
        L = int(0.5 * sr / hop_length)
    if 2*L+1 > n_frames:
        L = (n_frames - 1) // 2

    kernel = gaussian_checkerboard(L, sigma=L/2)

    for t in range(L, n_frames - L):
        block = SSM[t-L:t+L+1, t-L:t+L+1]
        novelty[t] = np.sum(kernel * block)

    return novelty


#This creates the kernel used later for the SSM math
def gaussian_checkerboard(L, sigma=1.0):
    x = np.arange(-L, L+1)
    y = np.arange(-L, L+1)
    x, y = np.meshgrid(x, y)

    g = np.exp(-(x**2 + y**2) / (2.0 * sigma**2))

    checkerboard = np.ones((2*L+1, 2*L+1))
    checkerboard[L+1:, :L] = -1
    checkerboard[:L, L+1:] = -1
    return g * checkerboard

# Computes the similarity between two frames
# Computes using a self similarity matrix and a checkerboard kernel to detect if frames are similar or not
# The greater the difference between the features of two frames, the more likely to be a phrase boundary
def compute_novelty(SSM, sr, L=None, hop_length=512):
    n_frames = SSM.shape[0]
    novelty = np.zeros(n_frames)
    if L is None:
        L = int(0.5 * sr / hop_length)

    for t in range(L, n_frames - L):
        left_block = SSM[t-L:t, t-L:t]
        right_block = SSM[t:t+L, t:t+L]

        novelty[t] = np.sum(np.abs(left_block - right_block))
    return novelty


#This help detects beatdrops in the song
def compute_spectral_flux(y, sr, hop_length=512, n_fft=2048):
    spectogram = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    spec_norm = librosa.util.normalize(spectogram, axis=0)

    flux = np.sqrt(np.sum(np.diff(spec_norm, axis=1)**2, axis=0))
    flux = (flux - np.mean(flux)) / np.std(flux)
    return flux



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
    mfcc_features = librosa.util.normalize(mfcc_features, axis=1)
    return mfcc_features


# Extracts the Chroma which is the quality of pitch
# Used to be categorized into one of twelve distinct pitch classes
def compute_chroma(y, sr):
    S = np.abs(librosa.stft(y))
    chroma = librosa.feature.chroma_stft(S=S, sr=sr)
    chroma = librosa.decompose.nn_filter(chroma)
    chroma = librosa.util.normalize(chroma, axis=0)
    return chroma

# This gets the audio waveform (y) and the sample rate (sr)
# y is the audio data sr is the scale
def preprocessing(song):
    y, sr = librosa.load(song['path'])
    y = librosa.util.normalize(y)
    y = highpass_filter(y, sr)
    y_harm, y_perc = librosa.effects.hpss(y)

    return y_harm, y_perc, sr

# Gets rid of any unwanted noise
# Used to "clean" the audio of background noises
# May not need but data will be different if turned on/off
def highpass_filter(y, sr, cutoff=100.0):
    b, a = butter(N=2,  Wn=cutoff / (sr / 2.0), btype='high', analog=False)
    y = filtfilt(b, a, y)
    return y

if __name__ == "__main__":
    folder = "Music/wav_files/"
    file_paths = glob.glob(os.path.join(folder, "*.wav"))
    loader = SongLoader()
    loader.load_songs(file_paths)

    songs = loader.get_songs()

    # Simple threading for each song to speed up the process
    max_threads = 10
    if len(songs) > max_threads:
        max_threads = len(songs)

    with Manager() as manager:
        lock = manager.Lock()
        if songs:
            # get_phrase_boundaries_complex(songs)
            with Pool(max_threads) as pool:
                pool.starmap(get_phrase_boundaries_complex, [(song, lock) for song in songs])
        else:
            print("no songs")




