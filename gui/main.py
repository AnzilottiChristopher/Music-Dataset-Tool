# this interface should:
# take a song, match to all other songs essentially
# first, match each phrase exit boundary with all the phrase entry boundaries of the other song
# - Apply the premade transition at each point (simple one for now), allow to provide a ranking and some comments
# second, match each phrase entry bounary with all the phrase exit boundaries of the other song
# - Apply the premade transition at each point (simple one for now), allow to provide a ranking and some comments
# ensure we skip over already completed pairs, so not really n^2
# once we give a ranking, it should update the json format to be trained with 

# actually this only requires us to loop through the songs once, so this shouldnt be all that bad as matching a song
# with the others will only require us to check the rest of the list, as it has already been compared to songs before it

# the gui should include a music player button, to play the transition, and can allow the transition to be replayed.
# of course, we should make a copy of the original json here as to not overwrite the results from before
# example output format from this tool

# {
#   "songs": [
#     {
#       "id": "stargazing",
#       "file": "stargazing-kygo.wav",
#       "features": {
#         "bpm": 98.85,
#         "key": "F",
#         "scale": "major",
#         "key_strength": 0.927,
#         "phrase_boundaries": {
#           "first": ["00:00", "00:17", "00:34", "00:52"],
#           "last": ["02:49", "03:08", "03:27", "03:47"]
#         }
#       }
#     },
#     {
#       "id": "wakemeup",
#       "file": "wakemeup-avicii.wav",
#       "features": { ... }
#     }
#   ],
#   "transitions": [
#     {
#       "song_a": "stargazing",
#       "song_b": "wakemeup",
#       "exit_a": "03:27",
#       "entry_b": "00:17",
#       "direction": "A→B",
#       "transition_preset": "simple_fade",
#       "rating": 4,
#       "comment": "Does not pair well"
#     }
#   ]
#

from app.window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.run()