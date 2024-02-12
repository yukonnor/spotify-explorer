import json

json_file_path = '/Users/connorschmidt/capstone-1/capstone-project-one-759b191e666f4d7d93b26845cc374036/research/every_noise_genres.json'

with open(json_file_path, 'r') as file:
    data = json.load(file)

genre_list = [genre["title"] for genre in data]
print(genre_list)
