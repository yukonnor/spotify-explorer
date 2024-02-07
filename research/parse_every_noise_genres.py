from html.parser import HTMLParser
import os
import json


class GenreParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside_desired_div = False
        self.genres = []   # list of genre objects (dicts for now)
        self.genre_div_attrs = {}
        self.genre_data = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            # Check if the 'id' attribute exists and starts with 'item'
            id_attribute = dict(attrs).get('id', '')
            if id_attribute.startswith('item'):
                self.inside_desired_div = True

                for key, value in attrs:
                    if key == 'preview_url':
                        self.genre_div_attrs[key] = value

                    if key == 'style':
                        style_dict = self.parse_style(value)
                        self.genre_div_attrs.update(style_dict)
                

    def handle_endtag(self, tag):
        if tag == 'div' and self.inside_desired_div:
            self.inside_desired_div = False
            self.genres.append({
                'genre': self.genre_data[0],
                **self.genre_div_attrs
            })
            # Reset current data and attributes for the next div
            self.genre_data = []
            self.genre_div_attrs = {}

    def handle_data(self, data):
        if self.inside_desired_div:
            self.genre_data.append(data)

    def parse_style(self, style_value):

        # Split the style string into segments based on semicolon
        style_segments = style_value.split(';')

        # Create a dictionary to store the property-value pairs
        style_dict = {}

        # Iterate over each segment and extract property-value pairs
        for segment in style_segments:
            # Split each segment into property and value based on colon
            property_value = segment.strip().split(':')
            
            # Ensure there are two elements after splitting (property and value)
            if len(property_value) == 2:
                property_name, property_value = map(str.strip, property_value)
                style_dict[property_name] = property_value


        print("Style Dict:", style_dict)

        # Now let's adjust the data to represent what it means
        parsed_dict = {}

        for key, value in style_dict.items(): 
            if key == "color":
                parsed_dict["energy_score"] = int(value[1:3], 16)  # parse "red" value of color
                parsed_dict["dynamic_variation_score"] = int(value[3:5], 16)  # parse "green" value of color 
                parsed_dict["instrumentalness_score"] = int(value[5:7], 16)  # parse "blue" value of color 
            elif key == "top":
                parsed_dict["organic_mechanical_score"] = int(value.replace('px', ''))  # lower score is more mechanical and electric, higher score is more organic / acoustic
            elif key == "left":
                parsed_dict["dense_spiky_score"] = int(value.replace('px', '')) # lower score is denser and more atmospheric, higher score is spikier and bouncier
            elif key == "font-size":
                parsed_dict["popularity_score"] = int(value.replace('%',''))  # higher score, more popular
                
        return parsed_dict


    
script_dir = os.path.dirname(os.path.realpath(__file__))
html_file_path = os.path.join(script_dir, 'every_noise_genre_snapshot_2024_02_07.html')

# Read the HTML content from the file
with open(html_file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()


# Run the parser
parser = GenreParser()
parser.feed(html_content)

# Save genre dictionary to file
with open('every_noise_genres.json', 'w') as file:
    json.dump(parser.genres, file)
