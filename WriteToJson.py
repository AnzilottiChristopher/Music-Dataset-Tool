import json
import glob
import os

from pathlib import Path


class writeToJson:
    def __init__(self, data=None, path=None):
        self.data = data
        self.path = path

    def resolve(self, value, attr_name):
        if value is not None:
            return value
        elif getattr(self, attr_name) is not None:
            return getattr(self, attr_name)
        else:
            raise ValueError(f"Data does not exist. Please input the data: {attr_name}")

    def create_file(self, path=None, data=None):
        data = self.resolve(data, "data")
        path = self.resolve(path, "path")

        try:
            with open(path, "w") as f:
                json.dump(self.data, f, ensure_ascii="utf-8")
        except:
            print("Error writing to file")

    def add_entry(self, data, path=None):
        path = self.resolve(path, "path")

        # Load existing data or create a new structure
        try:
            with open(path, "r") as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {"songs": []}

        # Ensure structure consistency
        if "songs" not in self.data:
            self.data["songs"] = []

        # Append new songs
        self.data["songs"].extend(data["songs"])

        # Write updated JSON
        with open(path, "w") as f:
            json.dump(self.data, f, indent=4, ensure_ascii="utf-8")

    def append_entry(self, data, entry, path=None):
        path = self.resolve(path, "path")
        song_name = data["song_name"]
        with open(path, "r+") as i:
            try:
                self.data = json.load(i)
            except:
                print("file not found")

        if entry.lower() == "song_name".lower():
            for i in self.data:
                if i["song_name"].lower() == song_name.lower():
                    self.data[0]["song_name"] = data[0]["song_name"]
        else:
            return

        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
