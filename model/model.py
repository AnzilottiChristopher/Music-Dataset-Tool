import json
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import pandas as pd

class TransitionModel:
    def __init__(self, json_path):
        self.json_path = json_path
        self.model = None 
        self.feature_names = None 
    
    # since the format is "XX:XX" as a str, we need to convert this to seconds and return a float 
    def _parse_phrase_boundaries(self, time):
        parts = time.split(":")
        total_time = float(parts[0]) * 60 + float(parts[1])
        return total_time
    
    # in the future, we can continously add more to this once we extract it 
    def _get_musical_distance(self, key_a, scale_a, key_b, scale_b):
        
        key_map = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
            'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
        }
        
        semitone_a = key_map.get(key_a, 0)
        semitone_b = key_map.get(key_b, 0)
        
        # now we need to calculate the the shortest distance around the circles of fifths
        semitone_diff = abs(semitone_a - semitone_b)
        if semitone_diff > 6:
            semitone_diff = 12 - semitone_diff
            
        # Same key and scale is ideal
        same_key = int(key_a == key_b)
        same_scale = int(scale_a == scale_b)
        
        # in music, the relative major/minor relationships is a difference of 3 semitones
        is_relative = int(semitone_diff == 3 and scale_a != scale_b)
        
        return {
            'semitone_distance': semitone_diff,
            'same_key': same_key,
            'same_scale': same_scale,
            'is_relative_key': is_relative
        }
        

    # so this will be used in a loop later to create the data for each boundary we need
    # so basically we loop through all of the phrase boundaries later obviously 
    # here, song_a will be the dict for song a and so forth
    def create_features(self, song_a, song_b, exit_boundary, entry_boundary, exit_idx=None, entry_idx = None):
        features = {}
        
        bpm_a = song_a['bpm']
        bpm_b = song_b['bpm']
        features['bpm_a'] = bpm_a
        features['bpm_b'] = bpm_b
        features['bpm_ratio'] = bpm_b / bpm_a if bpm_a > 0 else 1.0
        features['bpm_diff'] = abs(bpm_a - bpm_b)
        features['bpm_diff_pct'] = features['bpm_diff'] / bpm_a if bpm_a > 0 else 0
        
        # now we can add the key features, which we defined above
        key_features = self._get_musical_distance(song_a['key'], song_a['scale'], song_b['key'], song_b['scale'])
        features.update(key_features)
        
        features['key_strength_a'] = song_a['key_strength']
        features['key_strength_b'] = song_b['key_strength']
        features['key_strength_product'] = song_a['key_strength'] * song_b['key_strength']
        features['exit_time'] = exit_boundary
        features['entry_time'] = entry_boundary
        
        # we can use 1 if major, else 0
        features['scale_a_numeric'] = 1 if song_a['scale'] == 'major' else 0
        features['scale_b_numeric'] = 1 if song_b['scale'] == 'major' else 0
        
        # now we handle whether vocals were present
        features['exit_has_vocals'] = 0
        features['entry_has_vocals'] = 0
        features['both_have_vocals'] = 0
        features['neither_has_vocals'] = 0 
        
        if exit_idx is not None and 'exit_phrase_boundary_vocals' in song_a:
            exit_vocals = song_a['exit_phrase_boundary_vocals']
            if exit_idx < len(exit_vocals):
                features['exit_has_vocals'] = int(exit_vocals[exit_idx])
        
        if entry_idx is not None and 'entry_phrase_boundary_vocals' in song_b:
            entry_vocals = song_b['entry_phrase_boundary_vocals']
            if entry_idx < len(entry_vocals):
                features['entry_has_vocals'] = int(entry_vocals[entry_idx])
        
        # now we can combine these 
        features['both_have_vocals'] = features['exit_has_vocals'] * features['entry_has_vocals']
        features['neither_has_vocals'] = int(features['exit_has_vocals'] == 0 and features['entry_has_vocals'] == 0)
        
        return features
    
    def _find_boundary_index(self, song, time_seconds, boundary_type):
        # this will be a useful helper to find the index of the boundary
        if boundary_type == 'exit':
            boundary_key = 'last_phrase_boundaries'
        else:
            boundary_key = 'first_phrase_boundaries'
        
        if boundary_key not in song:
            return None
        
        boundaries = song[boundary_key]
        
        for idx, boundary_str in enumerate(boundaries):
            boundary_seconds = self._parse_phrase_boundaries(boundary_str)
            if abs(boundary_seconds - time_seconds) < 1.0: # in the future when these get precise
                return idx
        
        return None

    def create_training_set(self):
        
        with open(self.json_path, 'r') as f:
            data = json.load(f)
            
        # so now, we can just query the song from this dict once we come across it
        song_lookup = {}
        for song in data['songs']:
            song_lookup[song['song_name']] = song['features']
            
            
        # we will append features to X, targets (ratings) to y
        X_labels = []
        y_targets = []
        
        for transition in data['transitions']:
            song_a_name = transition['song_a']
            song_b_name = transition['song_b']
            
            # in theory, this should happen
            if song_a_name not in song_lookup or song_b_name not in song_lookup:
                print("In making the training set, found a song ranked for transition that was not preanalyzed.")
                continue
                
            song_a = song_lookup[song_a_name]
            song_b = song_lookup[song_b_name]
            
            exit_time = float(transition['exit_boundary'])
            entry_time = float(transition['entry_boundary'])
            rating = transition['rating']
            
            exit_idx = self._find_boundary_index(song_a, exit_time, 'exit')
            entry_idx = self._find_boundary_index(song_b, entry_time, 'entry')
            
            # Create features for this transition
            features = self.create_features(song_a, song_b, exit_time, entry_time, exit_idx, entry_idx)
            
            X_labels.append(list(features.values()))
            y_targets.append(rating)
        
        # we can store these names just to check to see what we have
        self.feature_names = list(features.keys())
        
        X = np.array(X_labels)
        y = np.array(y_targets)
        
        return X, y, self.feature_names
    
    def predict(self, X):
        if self.model is None:
            print('the model has not been trained yet!')
            return
        return self.model.predict(X)
    
    # config will be a dict that allows us to modify training by some dict we define before calling 
    def train(self, X, y, config=None):
        if config is None:
            # we will begin by just treating this as a regression task
            config = {
                'objective': 'reg:squarederror', 
                'max_depth': 4,                    
                'learning_rate': 0.1,
                'n_estimators': 100,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42
            }

        self.model = xgb.XGBRegressor(**config)
        self.model.fit(X, y)
        
        return self.model
    
    # so after training, we should be able to pass in two songs and have the model predict the rating 
    # at some boundary, but we will add a method for the predicted rankings later on
    def predict_transition_rating(self, song_a, song_b, exit_boundary, entry_boundary, exit_idx=None, entry_idx = None):
        features = self.create_features(song_a, song_b, exit_boundary, entry_boundary, exit_idx, entry_idx)
        X = np.array([list(features.values())])
        return self.predict(X)[0]
    
    def rank_boundaries_for_pair(self, song_a, song_b, exit_boundaries=None, entry_boundaries=None):
        results = []
        
        # Use boundaries from song features if not provided
        if exit_boundaries is None and 'last_phrase_boundaries' in song_a:
            exit_boundaries = [self.parse_time_to_seconds(b) for b in song_a['last_phrase_boundaries']]
        
        if entry_boundaries is None and 'first_phrase_boundaries' in song_b:
            entry_boundaries = [self.parse_time_to_seconds(b) for b in song_b['first_phrase_boundaries']]
        
        if exit_boundaries is None or entry_boundaries is None:
            raise ValueError("No boundaries provided or found in song features")
        
        # Get vocal presence info
        exit_vocals = song_a.get('exit_phrase_boundary_vocals', [False] * len(exit_boundaries))
        entry_vocals = song_b.get('entry_phrase_boundary_vocals', [False] * len(entry_boundaries))
        
        for exit_idx, exit_time in enumerate(exit_boundaries):
            for entry_idx, entry_time in enumerate(entry_boundaries):
                rating = self.predict_single_transition(
                    song_a, song_b, exit_time, entry_time, exit_idx, entry_idx
                )
                
                # Include vocal info in results for transparency
                exit_has_vocals = exit_vocals[exit_idx] if exit_idx < len(exit_vocals) else False
                entry_has_vocals = entry_vocals[entry_idx] if entry_idx < len(entry_vocals) else False
                
                results.append((exit_time, entry_time, rating, exit_has_vocals, entry_has_vocals))
        
        # Sort by predicted rating (descending)
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results
    
    def get_feature_importance(self):
        # we can see which features the models 
        if self.model is None:
            print('model is not trained yet, or something went wrong')
            return
            
        importance = self.model.feature_importances_
        if self.feature_names:
            return dict(zip(self.feature_names, importance))
        return importance
    
    def save_model(self, path):
        if self.model is None:
            print('No model to save!')
            return 
        
        self.model.save(path)
        
    def load_model(self, path):
        self.model = xgb.XGBRegressor()
        self.model.load_model(path)
        
        
    
if __name__ == "__main__":
    model = TransitionModel('../transition-results.json')
    
    X, y, features = model.create_training_set()
    # model.diagnose_training_data(X, y)
    model.train(X, y)
    
    feature_importance = model.get_feature_importance()
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    print(sorted_features) 