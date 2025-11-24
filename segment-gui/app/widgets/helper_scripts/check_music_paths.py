import json
from pathlib import Path

def check_consistency(json_path, folder_path):
    """
    Check if all songs in the JSON file exist in the specified folder.
    
    Args:
        json_path: Path to the JSON file containing song data
        folder_path: Path to the folder containing WAV files
    
    Returns:
        bool: True if all songs exist, False otherwise
    """
    try:
        # Load JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        songs = data.get('songs', [])
        if not songs:
            print("Warning: No songs found in JSON file")
            return False
        
        folder = Path(folder_path)
        if not folder.exists():
            print(f"Error: Folder does not exist: {folder_path}")
            return False
        
        missing_songs = []
        
        # Check each song
        for song in songs:
            song_name = song.get('song_name', '')
            if not song_name:
                print(f"Warning: Empty song name in JSON")
                continue
            
            song_path = folder / song_name
            if not song_path.exists():
                missing_songs.append(song_name)
                print(f"Missing: {song_name}")
        
        if missing_songs:
            print(f"\nTotal missing songs: {len(missing_songs)}")
            return False
        
        print(f"All {len(songs)} songs found in folder")
        return True
        
    except Exception as e:
        print(f"Error checking consistency: {e}")
        return False
