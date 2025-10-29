import os
import json 
from pathlib import Path


# we need to ensure that all of the song names in the json folder exist
# in the folder path before we go ahead and begin doing the rankings
def check_consistency(json_path, folder_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    songs_in_folder = os.listdir(folder_path)
    
    for song in data["songs"]:
        song_name = song["song_name"]
        
        if song_name not in songs_in_folder:
            print(f"The song {song_name} was not found in the library, ensure it exists")
            return False 
        
    return True
    
    
    
    
    
    
# if __name__ == "__main__":
#     json_path = Path("../../../../results.json").resolve()
#     folder_path = Path("../../../../Music/wav_files").resolve()
    
    
#     bool = check_consistency(json_path, folder_path)
#     print(bool)