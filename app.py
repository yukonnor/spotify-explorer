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

# Auth ################################################

# QUESTION: Put this and calls to API in separate file?
# QUESTION: Can I make a separate dev account using spotify free platform? I probably shouldn't use my personal acct.

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

@app.route('/playlist-inspector/<playlist_id>')
def playlist_inspector(playlist_id):
    
    playlist_name, playlist_url, tracks = get_playlist_data(playlist_id)

    return render_template('playlist-inspector.html', playlist_name=playlist_name, playlist_url=playlist_url, tracks=tracks)

# Misc Functions ################################################

# large playlist: 40z0ffEGmOcOjldmXI8ie6
# test playlist: 0qDBVeMndUkk7fwGfCuTR0

def get_playlist_data(playlist_id):

    # QUESTION: Get token each request or get it when I need it (after an hour)?
    access_token = get_token()

    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    headers = {'Authorization': f'Bearer {access_token}'}  
    fields =  'id, href, name, limit, tracks(next, offset, total, items(track(id, name, popularity, duration_ms, is_playable, preview_url, type, artists(id, name), album(name, href))))'
    params = {'fields': fields, 'market': 'US'} 

    # TODO: Handle status code != 200 & Private Playlists
    # TODO: Handle large playlists (next query and lists too long to handle)
    # TODO: Handle playlists with episodes instead of tracks (track.type == episode)
    # TODO: Handle tracks with multiple artists
    # TODO: Set width of columns to be constant arround trunc length
    response = requests.get(playlist_url, headers=headers, params=params)

    # If we didn't get a 200 status code, break out early
    if response.status_code != 200:
        print("Status code: ", response.status_code)
        print(response.json())

        return None, None, None

    payload = response.json()

    playlist_name = payload.get('name', {})
    playlist_url = f'https://open.spotify.com/playlist/{playlist_id}'

    # If the playlist doesn't have any tracks, break out early
    if not payload.get('tracks', False):
        print("No tracks found")
        print(payload)

        return playlist_name, playlist_url, None

    # if playlist 50 tracks are fewer, we can get the data we need from the response
    # otherwise we need to make calls to the playlist/tracks API.
    if payload['tracks']['total'] > 50: 
        items = get_playlist_tracks(playlist_id)  # TODO: write this function
    else: 
        items = payload.get('tracks', {}).get('items', {})

    # flatten results into track data
    tracks = [item["track"] for item in items]

    # process data to our liking:
    for track in tracks:
        # add duration in minutes & seconds
        ms = track['duration_ms'] 
        track['duration']= f"{(ms//1000)//60}:{(ms//1000)%60}" 

    # Get track audio features and append to tracks
    track_ids = [track['id'] for track in tracks]
    track_ids_param = ','.join(track_ids)

    track_audio_features_url = 'https://api.spotify.com/v1/audio-features'
    params = {'ids': track_ids_param} 

    response = requests.get(track_audio_features_url, headers=headers, params=params)
    track_audio_features = response.json().get('audio_features', {})
    
    # Add audio features to tracks dict
    for index, track in enumerate(track_audio_features):
        if track: 
            tracks[index]["danceability"] = track.get("danceability", None)
            tracks[index]["energy"] = track.get("energy", None)

    # Get artist details (namely genres) and append to tracks
    artist_ids = [track['artists'][0]['id'] for track in tracks]
    aritst_ids_param = ','.join(artist_ids)

    print("Artists IDS param: ", aritst_ids_param)

    artists_url = 'https://api.spotify.com/v1/artists'
    params = {'ids': aritst_ids_param} 

    response = requests.get(artists_url, headers=headers, params=params)
    artists = response.json().get('artists', {})

    print("Artists API Call Response: ", response.json())

    # Add artist metadata to tracks dict
    for index, artist in enumerate(artists):
        if artist: 
            tracks[index]["artist_followers"] = artist.get("followers", None).get("total", None)
            tracks[index]["artist_popularity"] = artist.get("popularity", None)
            tracks[index]["artist_genres"] = artist.get("genres", None)

    return playlist_name, playlist_url, tracks




# Run ################################################

if __name__ == "__main__":
    app.run(debug=True)