import json
import os

current_directory = os.getcwd()
relative_path = 'research/every_noise_genres.json'

json_file_path = os.path.join(current_directory, relative_path)

with open(json_file_path, 'r') as file:
    # Load the JSON data into a Python dictionary
    genre_dict_list = json.load(file)

#print(genre_dict_list)
