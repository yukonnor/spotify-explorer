from flask import Flask, request, render_template, redirect, flash, session
from authlib.integrations.flask_client import OAuth
from config import FLASK_SECRET_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

# Spotify OAuth setup for client credentials flow
def gen_headers(access_token):
    return {'Authorization': f'Bearer {access_token}'}   

# TODO: Introduce user auth so that they can see their own private playlists and create new playlists on their account

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

@app.route('/')
def home():
    """Render the home page."""
    return render_template('home.html')

@app.route('/genres')
def genre_index():
    """Render the genre index page."""
    return render_template('genre-index.html')

@app.route('/get-playlist')
def get_playlist():
    """Process the 'get playlist' form, redirecting user to the playlist inspector page for the playlist."""

    playlist_link = request.args.get('playlistLink')

    if not playlist_link or not playlist_link.startswith('https://open.spotify.com/playlist/'):
        flash("Looks like the playlist link wasn't in the expected format. Please try again.", "warning")
        return redirect('/')

    playlist_id = extract_playlist_id(playlist_link)

    return redirect(f'/playlist-inspector/{playlist_id}')

@app.route('/playlist-inspector/<playlist_id>')
def playlist_inspector(playlist_id):
    
    playlist_name, playlist_url, tracks = get_playlist_data(playlist_id)

    # TODO: show a genre count table (maybe broken down by parent genre vs specific genre)

    return render_template('playlist-inspector.html', playlist_name=playlist_name, playlist_url=playlist_url, tracks=tracks)

# Misc Functions ################################################

# test playlist: 0qDBVeMndUkk7fwGfCuTR0
# medium playlist: 7b7WSmGwf101AiXNyrMKEO
# large playlist: 40z0ffEGmOcOjldmXI8ie6
# cowpunk: 37i9dQZF1EIgtiaACXv6tQ

def get_playlist_data(playlist_id):

    # QUESTION: Get token each request or get it when I need it (after an hour)?
    access_token = get_token()

    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    fields =  'id, href, name, limit, tracks(next, offset, total, items(track(id, name, popularity, duration_ms, is_playable, preview_url, type, artists(id, name), album(name, href))))'
    params = {'fields': fields, 'market': 'US'} 

    # TODO: Handle status code != 200 & Private Playlists
    # TODO: Handle large playlists (next query and lists too long to handle)
    # TODO: Handle playlists with episodes instead of tracks (track.type == episode)
    # TODO: Handle tracks with multiple artists
    # TODO: Set width of columns to be constant arround trunc length
    response = requests.get(playlist_url, headers=gen_headers(access_token), params=params)

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
        print("Playlist has more than 50 tracks...")
        tracks = get_playlist_tracks(playlist_id, access_token) 
    else: 
        items = payload.get('tracks', {}).get('items', {})
        tracks = [item["track"] for item in items] # flatten results into track data
        tracks = get_track_audio_features(tracks, access_token)  # Get track audio features and append to tracks
        tracks = get_artist_details(tracks, access_token)

    # process data to our liking:
    for track in tracks:
        # add duration in minutes & seconds
        ms = track['duration_ms'] 
        track['duration']= f"{(ms//1000)//60}:{(ms//1000)%60}" 

    return playlist_name, playlist_url, tracks

def get_playlist_tracks(playlist_id, access_token):

    tracks = []

    playlist_tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks' 
    fields =  'next, offset, total, items(track(id, name, popularity, duration_ms, is_playable, preview_url, type, artists(id, name), album(name, href)))'
    offset_amt = 0

    # Loop until we get 
    while playlist_tracks_url != None: 
        params = {'fields': fields, 'market': 'US', 'limit': 50, 'offset': {offset_amt}} 

        response = requests.get(playlist_tracks_url, headers=gen_headers(access_token), params=params)

        # If we didn't get a 200 status code, break out early
        if response.status_code != 200:
            print("Status code: ", response.status_code)
            print(response.json())
            return None

        response = requests.get(playlist_tracks_url, headers=gen_headers(access_token), params=params)
        payload = response.json()

        items = payload.get('items', {})

        tracks_batch = [item["track"] for item in items] # flatten results into track data

        tracks_batch = get_track_audio_features(tracks_batch, access_token)
        tracks_batch = get_artist_details(tracks_batch, access_token)
       
        # add new track sublist to the tracks list
        tracks = tracks + tracks_batch

        playlist_tracks_url = response.json().get('next', None)
        offset_amt += 50  # TODO: not sure we need this as the next URL includes all of the params
        
        # emergecy breakout:
        if offset_amt > 1000:
            next = None

    return tracks

def get_track_audio_features(tracks, access_token):
    track_ids = [track['id'] for track in tracks]
    track_ids_param = ','.join(track_ids)

    track_audio_features_url = 'https://api.spotify.com/v1/audio-features'
    params = {'ids': track_ids_param} 

    response = requests.get(track_audio_features_url, headers=gen_headers(access_token), params=params)
    track_audio_features = response.json().get('audio_features', {})
    
    # Add audio features to tracks dict
    for index, track in enumerate(track_audio_features):
        if track: 
            tracks[index]["danceability"] = track.get("danceability", None)
            tracks[index]["energy"] = track.get("energy", None)

    return tracks

def get_artist_details(tracks, access_token):
    """ Get artist details (namely popularity & genres) and append to tracks """
    artist_ids = [track['artists'][0]['id'] for track in tracks]
    aritst_ids_param = ','.join(artist_ids)

    artists_url = 'https://api.spotify.com/v1/artists'
    params = {'ids': aritst_ids_param} 

    response = requests.get(artists_url, headers=gen_headers(access_token), params=params)
    artists = response.json().get('artists', {})

    # Add artist metadata to tracks dict
    for index, artist in enumerate(artists):
        if artist: 
            tracks[index]["artist_followers"] = artist.get("followers", None).get("total", None)
            tracks[index]["artist_popularity"] = artist.get("popularity", None)
            tracks[index]["artist_genres"] = artist.get("genres", None)

    return tracks

def extract_playlist_id(link):
    parts = link.split('/')

    # Find the index of 'playlist' in the parts list
    playlist_index = parts.index('playlist')

    # Extract the playlist ID from the next part
    playlist_id = parts[playlist_index + 1].split('?')[0]

    return playlist_id

# Run ################################################

if __name__ == "__main__":
    app.run(debug=True)