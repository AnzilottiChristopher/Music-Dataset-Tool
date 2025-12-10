import glob
import json
import os
import librosa
import numpy as np

from BeatNet.BeatNet import BeatNet
from DatasetTool import SongLoader


class BeatDrop:
    def __init__(self, path, downbeat_times, beat_times, beats, downbeats):
        self.path = path
        self.downbeats = downbeats
        self.beat_times = beat_times
        self.beats = beats
        self.downbeat_times = downbeat_times

    def downBeatTimesAtSegment(self, segment, file_path="segmented_results.json"):
        with open(file_path, "r") as f:
            data = json.load(f)

        # song_filename = self.path.split("/")[-1]
        song_filename = os.path.basename(self.path)
        song_segment_set = data["songs"]

        downbeats_in_segment = []

        for song_name in song_segment_set:
            if song_filename == song_name["song_name"]:
                segs = song_name.get("segments", {})

                segment_times = segs.get(segment)

                if not segment_times:
                    return []

                start, end = segment_times
                downbeats_in_segment = [
                    float(b) for b in self.downbeat_times if start <= b <= end
                ]
                return downbeats_in_segment

        return []

    def getPath(self):
        return self.path

    def getDownbeats(self):
        return self.downbeats

    def getBeat_Times(self):
        return self.beat_times

    def getBeats(self):
        return self.beats

    def getDownbeat_Times(self):
        return self.downbeat_times


def beatnet_detection(audio_path, model_id=1, inference_model="DBN"):
    estimator = BeatNet(
        model_id, mode="offline", inference_model=inference_model, plot=[]
    )
    output = estimator.process(audio_path)

    beat_times = output[:, 0].tolist()
    downbeat_times = output[:, 1].tolist()

    return beat_times, downbeat_times


if __name__ == "__main__":
    loader = SongLoader()
    # Change this to the correct file path that you want
    folder = "Music/Chris_Music/"
    file_paths = glob.glob(os.path.join(folder, "*.wav"))
    loader.load_songs(file_paths)

    songs = loader.get_songs()
    songBeats = []

    # Will go through all the songs and have beatnet run an analysis on them getting the beats and downbeats of the song
    for song in songs:
        beats, downbeats = beatnet_detection(song["path"])
        beats_time = np.array(beats)
        downbeatFlags = np.array(downbeats)
        downbeat_times = beats_time[downbeatFlags == 1.0]
        beat = BeatDrop(song["path"], downbeat_times, beats_time, beats, downbeats)
        songBeats.append(beat)
