from html.parser import HTMLParser
import os


class GenreParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside_desired_div = False
        self.desired_div_data = []
        self.current_div_attrs = {}
        self.current_data = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            # Check if the 'id' attribute exists and starts with 'item'
            id_attribute = dict(attrs).get('id', '')
            if id_attribute.startswith('item'):
                self.inside_desired_div = True

                for key, value in attrs:
                    if key == 'preview_url':
                        self.current_div_attrs[key] = value

                    if key == 'style':
                        style_dict = self.parse_style(value)
                        self.current_div_attrs.update(style_dict)
                

    def handle_endtag(self, tag):
        if tag == 'div' and self.inside_desired_div:
            self.inside_desired_div = False
            self.desired_div_data.append({
                'data': ''.join(self.current_data),
                **self.current_div_attrs
            })
            # Reset current data and attributes for the next div
            self.current_data = []
            self.current_div_attrs = {}

    def handle_data(self, data):
        if self.inside_desired_div:
            data = data.replace("» ","")
            self.current_data.append(data)

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

        # # Extract specific values for 'top', 'left', and 'font-size'
        # top_value = style_dict.get('top', None)
        # left_value = style_dict.get('left', None)
        # font_size_value = style_dict.get('font-size', None)
                
        # self.current_div_attrs['popularity_score'] =
        # self.current_div_attrs['organic_mechanical_score'] =   # higher score is more mechanical and electric, lower score is more organic / acoustic
        # self.current_div_attrs['dense_spiky_score'] =   # higher score is spikier and bouncier, lower score is denser and more atmospheric 
                
        return style_dict


    
script_dir = os.path.dirname(os.path.realpath(__file__))
html_file_path = os.path.join(script_dir, 'every_noise_genre_snapshot_2024_02_07.html')

# Read the HTML content from the file
with open(html_file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

parser = GenreParser()
parser.feed(html_content)

print(parser.desired_div_data)