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
    """ Fetch data from Spotify API using client credentials """

    print("Getting access token...")
    
    token_request_params = {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    }

    # Make the request and obtain the response
    response = requests.post(spotify.access_token_url, data=token_request_params)

    if response.status_code != 200:
        print("Status code: ", response.status_code)
        print(response.json())

        return None

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

    # QUESTION: Get token each request or get it when I need it (after an hour)?
    access_token = get_token()

    playlist_info_payload = get_playlist_info(playlist_id, access_token)

    if not playlist_info_payload:
        flash("Wasn't able to fetch the playlist :/  (Devs: see logs for details)", "warning")
        return redirect('/')
    
    playlist_name = playlist_info_payload.get('name', {})
    playlist_link = f'https://open.spotify.com/playlist/{playlist_id}'
    playlist_img_url = None

    if playlist_info_payload["images"]:
        playlist_img_url = playlist_info_payload["images"][0]["url"]

    tracks = get_playlist_tracks(playlist_id, access_token)

    # TODO: show a genre count table (maybe broken down by parent genre vs specific genre)
    # TODO: implement Bootstrap table for sorting and sticky headers

    return render_template('playlist-inspector.html', playlist_name=playlist_name, playlist_link=playlist_link, playlist_img_url=playlist_img_url, tracks=tracks)

@app.route('/genre-inspector/<genre_title>')
def genre_inspector(genre_title):

    print(f"Generating genre inspector page for {genre_title}...")

    source = request.args.get('source')

    access_token = get_token()

    if source == 'spotify' or source == 'thesoundsofspotify':
        playlist_id = get_playlist_by_genre(genre_title, source, access_token)
    else: 
        flash("I don't currently support the type of playlist you were looking for.", "warning")
        return redirect('/')

    playlist_info_payload = get_playlist_info(playlist_id, access_token)

    if not playlist_info_payload:
        flash("Wasn't able to fetch the playlist :/  (Devs: see logs for details)", "warning")
        return redirect('/')
    
    playlist_name = playlist_info_payload.get('name', {})
    playlist_link = f'https://open.spotify.com/playlist/{playlist_id}'
    playlist_img_url = None

    if playlist_info_payload["images"]:
        playlist_img_url = playlist_info_payload["images"][0]["url"]

    tracks = get_playlist_tracks(playlist_id, access_token)

    return render_template('genre-inspector.html', genre_title=genre_title, source=source, playlist_name=playlist_name, playlist_link=playlist_link, playlist_img_url=playlist_img_url, tracks=tracks)


# Misc Functions ################################################

# test playlist: 0qDBVeMndUkk7fwGfCuTR0
# medium playlist: 7b7WSmGwf101AiXNyrMKEO
# large playlist: 40z0ffEGmOcOjldmXI8ie6
# cowpunk: 37i9dQZF1EIgtiaACXv6tQ

def get_playlist_info(playlist_id, access_token):
    """Get metadata about a playlist from the Spotify API."""

    # TODO: Handle status code != 200 (Access Token, Private Playlists, ID not found, etc)
    # TODO: Handle large playlists (next query and lists too long to handle)
    # TODO: Handle playlists with episodes instead of tracks (track.type == episode)
    # TODO: Handle tracks with multiple artists
    # TODO: Set width of columns to be constant arround trunc length

    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    fields =  'id, href, name, images'
    params = {'fields': fields, 'market': 'US'} 

    response = requests.get(playlist_url, headers=gen_headers(access_token), params=params)

    if response.status_code != 200:
        print("Status code: ", response.status_code)
        print(response.json())

        return None

    payload = response.json()

    return payload

def get_playlist_tracks(playlist_id, access_token):
    """Get metadata about playlist tracks from the Spotify API.
       Append audio features and artist genre & popularity."""

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

     # process data to our liking:
    for track in tracks:
        # add duration in minutes & seconds
        ms = track['duration_ms'] 
        track['duration']= f"{(ms//1000)//60}:{(ms//1000)%60}" 

        if track.get('tempo', None): 
            track['tempo'] = round(track['tempo'])

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
            tracks[index]["acousticness"] = track.get("acousticness", None)
            tracks[index]["instrumentalness"] = track.get("instrumentalness", None)
            tracks[index]["tempo"] = track.get("tempo", None)
            tracks[index]["positivity"] = track.get("valence", None)

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

def get_playlist_by_genre(genre_title, source, access_token):
    """Find either the official Spotify playist or "Every Noise's" thesoundsofspotify playlist for the genre using the Spotify Search API."""

    print("Looking for genre playlists for genre: ", genre_title)

    search_url = "https://api.spotify.com/v1/search"

    if source == 'spotify':
        query = f'{genre_title} mix'
    elif source == 'thesoundsofspotify':
        query = f'the sound of {genre_title}'

    params = {'q':query,'type':'playlist', 'market':'US', 'limit':'10'} 

    response = requests.get(search_url, headers=gen_headers(access_token), params=params)
    playlist_search_results = response.json().get('playlists', {}).get('items', {})

    for playlist in playlist_search_results:
        owner_id = playlist['owner']['id']
        playlist_title = playlist['name']
        if owner_id == source and genre_title in playlist_title.lower():
            return playlist['id']

    # If no offcial spotify or 'every noise' playlist found, return None 
    return None





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