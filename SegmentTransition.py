import glob
import os
import librosa
import numpy as np

from BeatNet.BeatNet import BeatNet
from DatasetTool import SongLoader


if __name__ == "__main__":
    loader = SongLoader()
    folder = "Music/wav_files/"
    file_paths = glob.glob(os.path.join(folder, "*.wav"))
    loader.load_songs(file_paths)

    songs = loader.get_songs()
