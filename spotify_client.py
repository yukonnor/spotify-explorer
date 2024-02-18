from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import requests

# Question / TODO: Create a tracks class? 

# test playlist: 0qDBVeMndUkk7fwGfCuTR0
# medium playlist: 7b7WSmGwf101AiXNyrMKEO
# large playlist: 40z0ffEGmOcOjldmXI8ie6
# cowpunk: 37i9dQZF1EIgtiaACXv6tQ


class SpotifyClient:
    def __init__(self):
        
        self.access_token = 'tbd'   # QUESTION: Is this needed? 
        self.get_token()

    def get_token(self):
        """ Get API token used to get data from Spotify using client credentials """

        print("Getting access token...")
        
        TOKEN_REQUEST_PARAMS = {
            'grant_type': 'client_credentials',
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET,
        }

        ACCESS_TOKEN_URL = 'https://accounts.spotify.com/api/token'

        # Make the request and obtain the response
        response = requests.post(ACCESS_TOKEN_URL, data=TOKEN_REQUEST_PARAMS)

        if response.status_code != 200:
            print("Status code: ", response.status_code)
            print(response.json())

            return None

        response_data = response.json()

        # TODO: Check if response_data includes access_token
        access_token = response_data['access_token']

        self.access_token = access_token
        self.headers = self.gen_headers()

    def gen_headers(self):
        return {'Authorization': f'Bearer {self.access_token}'}  

    def get_playlist_info(self, playlist_id):
        """Get metadata about a playlist from the Spotify API."""

        # TODO: Handle status code != 200 (Access Token, Private Playlists, ID not found, etc)
        # TODO: Handle large playlists (next query and lists too long to handle)
        # TODO: Handle playlists with episodes instead of tracks (track.type == episode)
        # TODO: Handle tracks with multiple artists
        # TODO: Set width of columns to be constant arround trunc length

        playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
        fields =  'id, href, name, images'
        params = {'fields': fields, 'market': 'US'} 

        response = requests.get(playlist_url, headers=self.headers, params=params)
   
        if self.should_retry(response):
            # get new toke and try request again
            self.get_token()
            response = requests.get(playlist_url, headers=self.headers, params=params)

            # if fails again, back out
            if response.status_code not in [200, 201, 202, 204]:
                self.handle_error_status_code()        
            
        elif response.status_code not in [200, 201, 202, 204]:
            self.handle_error_status_code
        
        return response.json() if response.status_code in [200, 201, 202, 204] else None

    def get_playlist_tracks(self, playlist_id):
        """Get metadata about playlist tracks from the Spotify API.
        Append audio features and artist genre & popularity."""

        tracks = []

        playlist_tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks' 
        fields =  'next, offset, total, items(track(id, name, popularity, duration_ms, is_playable, preview_url, type, artists(id, name), album(name, href)))'
        offset_amt = 0

        # Loop until we get 
        while playlist_tracks_url != None: 
            params = {'fields': fields, 'market': 'US', 'limit': 50, 'offset': {offset_amt}} 

            response = requests.get(playlist_tracks_url, headers=self.headers, params=params)

            if self.should_retry(response):
                # get new toke and try request again
                self.get_token()
                response = requests.get(playlist_tracks_url, headers=self.headers, params=params)

                # if fails again, back out
                if response.status_code not in [200, 201, 202, 204]:
                    self.handle_error_status_code()   
                    return None     
                
            elif response.status_code not in [200, 201, 202, 204]:
                self.handle_error_status_code
                return None
            
            payload = response.json()

            items = payload.get('items', {})

            # flatten results into track data
            tracks_batch = [item["track"] for item in items] 

            # clean up the data to our liking
            for track in tracks_batch:
                track['album'] = track['album']['name'] 
                track['artist_name'] = track['artists'][0]['name'] 
                track['artist_id'] = track['artists'][0]['id'] 

            tracks_batch = self.get_track_audio_features(tracks_batch)
            tracks_batch = self.get_tracks_artists(tracks_batch)
        
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
            track['duration']= convert_ms_to_mins(track['duration_ms'])

        return tracks

    def get_track_audio_features(self, tracks):
        """ Get track audiot features from spotify and append them to the tracks list """
        track_ids = [track['id'] for track in tracks]
        track_ids_param = ','.join(track_ids)

        track_audio_features_url = 'https://api.spotify.com/v1/audio-features'
        params = {'ids': track_ids_param} 

        response = requests.get(track_audio_features_url, headers=self.headers, params=params)

        if self.should_retry(response):
            # get new toke and try request again
            self.get_token()
            response = requests.get(track_audio_features_url, headers=self.headers, params=params)

            # if fails again, back out
            if response.status_code not in [200, 201, 202, 204]:
                self.handle_error_status_code()   
                return None     
            
        elif response.status_code not in [200, 201, 202, 204]:
            self.handle_error_status_code
            return None

        track_audio_features = response.json().get('audio_features', {})
        
        # Add audio features to tracks dict
        for index, track in enumerate(track_audio_features):
            if track: 
                tracks[index]["danceability"] = round(track.get("danceability", None), 3) # float: 0.0 - 1.0
                tracks[index]["energy"] = round(track.get("energy", None), 3) # float: 0.0 - 1.0
                tracks[index]["acousticness"] = round(track.get("acousticness", None), 3) # float: 0.0 - 1.0
                tracks[index]["instrumentalness"] = round(track.get("instrumentalness", None), 3) # float: 0.0 - 1.0
                tracks[index]["tempo"] = round(track.get("tempo", None))
                tracks[index]["positivity"] = round(track.get("valence", None), 3)  # float: 0.0 - 1.0

        return tracks

    def get_tracks_artists(self, tracks):
        """ Get artist details (namely popularity & genres) and append to tracks """
        artist_ids = [track.get('artist_id', None) for track in tracks]
        aritst_ids_param = ','.join(artist_ids)

        artists_url = 'https://api.spotify.com/v1/artists'
        params = {'ids': aritst_ids_param} 

        response = requests.get(artists_url, headers=self.headers, params=params)

        if self.should_retry(response):
            # get new toke and try request again
            self.get_token()
            response = requests.get(artists_url, headers=self.headers, params=params)

            # if fails again, back out
            if response.status_code not in [200, 201, 202, 204]:
                self.handle_error_status_code()   
                return None     
            
        elif response.status_code not in [200, 201, 202, 204]:
            self.handle_error_status_code
            return None

        artists = response.json().get('artists', {})

        # Add artist metadata to tracks dict
        for index, artist in enumerate(artists):
            if artist: 
                tracks[index]["artist_followers"] = artist.get("followers", None).get("total", None)
                tracks[index]["artist_popularity"] = artist.get("popularity", None)
                tracks[index]["artist_genres"] = artist.get("genres", None)

        return tracks
    
    def get_artist_details(self, artist_id):
        """ Get the details for a singluar artist """
        artist_url = f'https://api.spotify.com/v1/artists/{artist_id}'

        response = requests.get(artist_url, headers=self.headers)

        if self.should_retry(response):
            # get new toke and try request again
            self.get_token()
            response = requests.get(artist_url, headers=self.headers)

            # if fails again, back out
            if response.status_code not in [200, 201, 202, 204]:
                self.handle_error_status_code()   
                return None     
            
        elif response.status_code not in [200, 201, 202, 204]:
            self.handle_error_status_code
            return None

        artist_payload = response.json()

        return artist_payload
    
    def get_artist_top_tracks(self, artist_id):
        """ Get the top tracks for a particular artist """
        artist_top_tracks_url = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks'
        params = {'ids': artist_id, 'market': 'US'} 

        response = requests.get(artist_top_tracks_url, headers=self.headers, params=params)

        if self.should_retry(response):
            # get new toke and try request again
            self.get_token()
            response = requests.get(artist_top_tracks_url, headers=self.headers)

            # if fails again, back out
            if response.status_code not in [200, 201, 202, 204]:
                self.handle_error_status_code()   
                return None     
            
        elif response.status_code not in [200, 201, 202, 204]:
            self.handle_error_status_code
            return None

        top_tracks_payload = response.json().get('tracks')

        # clean up the data to our liking
        for track in top_tracks_payload:
            track['album'] = track['album']['name'] 
            
            # add duration in minutes & seconds
            track['duration']= convert_ms_to_mins(track['duration_ms'])

        return top_tracks_payload
        


    def get_playlist_by_genre(self, genre_title, source):
        """ Find either the official Spotify playist or "Every Noise's" thesoundsofspotify playlist for the genre using the Spotify Search API. """

        print("Looking for genre playlists for genre: ", genre_title)

        search_url = "https://api.spotify.com/v1/search"

        if source == 'spotify':
            query = f'{genre_title} mix'
        elif source == 'thesoundsofspotify':
            query = f'the sound of {genre_title}'

        params = {'q':query,'type':'playlist', 'market':'US', 'limit':'10'} 

        response = requests.get(search_url, headers=self.headers, params=params)

        # Check if we got an error
        if self.should_retry(response):
            # get new toke and try request again
            self.get_token()
            response = requests.get(search_url, headers=self.headers, params=params)

            # if fails again, back out
            if response.status_code not in [200, 201, 202, 204]:
                self.handle_error_status_code()   
                return None     
            
        elif response.status_code not in [200, 201, 202, 204]:
            self.handle_error_status_code
            return None

        # Got a successful response. Continue...
        playlist_search_results = response.json().get('playlists', {}).get('items', {})

        for playlist in playlist_search_results:
            owner_id = playlist['owner']['id']
            playlist_title = playlist['name']
            if owner_id == source and genre_title in playlist_title.lower():
                return playlist['id']

        # If no offcial spotify or 'every noise' playlist found, return None 
        return None 
    
    def should_retry(self, response):
        return response.status_code == 401 and response.json()['error']['message'] == "The access token expired"
    
    def handle_error_status_code(self, response):
        print("Status code: ", response.status_code)
        print(response.json())

        

def convert_ms_to_mins(ms):
    min = (ms//1000)//60
    sec = (ms//1000)%60
    if sec >=0 and sec < 10:
        sec = f'0{sec}'

    return f'{min}:{sec}'