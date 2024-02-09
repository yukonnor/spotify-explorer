from flask import Flask, render_template
from authlib.integrations.flask_client import OAuth
from config import FLASK_SECRET_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

# Spotify OAuth setup for client credentials flow
oauth = OAuth(app)
spotify = oauth.register(
    name='spotify',
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    authorize_url=None,
    authorize_params=None,
    access_token_url='https://accounts.spotify.com/api/token',
    redirect_uri=None,
    client_kwargs={'scope': 'user-library-read'}  # Adjust the scope as needed
)

print("Spotify OAuth Object: ", spotify)

# Auth ################################################

def get_token():
    # Fetch data from Spotify API using client credentials
    token_request_params = {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    }

    # Make the request and obtain the response
    response = requests.post(spotify.access_token_url, data=token_request_params)

    response_data = response.json()

    # TODO: Check if response_data includes access_token
    access_token = response_data['access_token']

    return access_token

################################################

@app.route('/test-connection')
def spotify_index():
    
    access_token = get_token()

    # Use the access token to make API requests
    categories_url = 'https://api.spotify.com/v1/browse/categories'
    headers = {'Authorization': f'Bearer {access_token}'}   
    params = {'limit': 20, 'offset': 0} 

    # TODO: Handle status code != 200
    categories_response = requests.get(categories_url, headers=headers, params=params)
    categories = categories_response.json().get('categories', {}).get('items', [])

    return render_template('category-index.html', categories=categories)

@app.route('/playlist-analyzer/<playlist_id>')
def playlist_analyzer(playlist_id):
    
    access_token = get_token()
    
    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    headers = {'Authorization': f'Bearer {access_token}'}  
    fields =  'id, href, name, limit, tracks(next, offset, total, items(track(id, name, popularity, is_playable, preview_url, type, artists(id, name), album(name, href))))'
    params = {'fields': fields, 'market': 'US'} 

    # TODO: Handle status code != 200 & Private Playlists
    # TODO: Handle large playlists (next query and lists too long to handle)
    # TODO: Handle playlists with episodes instead of tracks (track.type == episode)
    # TODO: Handle tracks with multiple artists
    response = requests.get(playlist_url, headers=headers, params=params)
    playlist_name = response.json().get('name', {})
    playlist_url = f'https://open.spotify.com/playlist/{playlist_id}'
    items = response.json().get('tracks', {}).get('items', {})

    return render_template('playlist-analyzer.html', playlist_name=playlist_name, playlist_url=playlist_url, items=items)

if __name__ == "__main__":
    app.run(debug=True)