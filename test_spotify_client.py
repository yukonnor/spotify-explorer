from unittest import TestCase

from spotify_client import SpotifyClient
import requests
import time

# spin up client before tests
spotify = SpotifyClient()

class SpotifyClientTests(TestCase):
    """Tests for the Spotify Explorer API integration and helper methods."""

    def setUp(self):
         """Set up before each test"""
         self.ex_artist_id = "3u1ulLq00Y3bfmq9FfjsPu"
         self.ex_short_playlist_id = "37i9dQZF1EIgtiaACXv6tQ"
         self.ex_long_playlist_id = "6VbtVCyMUz0eoiWGl2r6g7"
         self.ex_track_id = "7cGwqXXVav9Tg0XNoONPlo"
            
    def tearDown(self):
        """Clean up after each test"""
        pass

    def test_token_retrieval(self):
        """Does the spotify instance have a valid access token associated with it?"""
        
        self.assertIsNotNone(spotify.access_token)

        artists_url = f'https://api.spotify.com/v1/artists/{self.ex_artist_id}'
        response = requests.get(artists_url, headers=spotify.headers)

        self.assertEqual(response.status_code, 200)

    def test_get_playlist_info(self):
        """Does the getting playlist info work?"""

        payload = spotify.get_playlist_info(self.ex_short_playlist_id)

        self.assertEqual(payload['id'], self.ex_short_playlist_id)

    def test_invalid_token(self):
        """If token is invalid, does fetching new token work?"""
        
        spotify.access_token = 'invalidtoken12345'
        payload = spotify.get_playlist_info(self.ex_short_playlist_id)

        self.assertEqual(payload['id'], self.ex_short_playlist_id)

    def test_get_playlist_tracks(self):
        """Does the getting playlist tracks work?"""

        playlist_tracks_url = f'https://api.spotify.com/v1/playlists/{self.ex_short_playlist_id}/tracks' 
        fields =  'next, offset, total, items(track(id, name, popularity, duration_ms, is_playable, preview_url, type, artists(id, name), album(name, href)))'
        params = {'fields': fields, 'market': 'US', 'limit': 50} 
        response = requests.get(playlist_tracks_url, headers=spotify.headers, params=params)
        local_payload = response.json()

        time.sleep(1) # sleep to avoid rate limits
        client_payload = spotify.get_playlist_tracks(self.ex_short_playlist_id)

        self.assertEqual(len(client_payload), local_payload['total'])

    def test_get_playlist_tracks_long(self):
        """Does the getting playlist tracks for a playlist with more than 100 tracks work?"""

        playlist_tracks_url = f'https://api.spotify.com/v1/playlists/{self.ex_long_playlist_id}/tracks' 
        fields =  'next, offset, total, items(track(id, name, popularity, duration_ms, is_playable, preview_url, type, artists(id, name), album(name, href)))'
        params = {'fields': fields, 'market': 'US', 'limit': 50} 
        response = requests.get(playlist_tracks_url, headers=spotify.headers, params=params)
        local_payload = response.json()

        time.sleep(1) # sleep to avoid rate limits
        client_payload = spotify.get_playlist_tracks(self.ex_long_playlist_id)

        self.assertEqual(len(client_payload), local_payload['total'])

    def test_get_track_audio_features(self):
        """Does the getting track audio features work?"""

        payload = spotify.get_track_audio_features([{'id': self.ex_track_id}])

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]['tempo'], 112)

    def test_get_artist_details(self):
            """Does the getting artist details work?"""

            payload = spotify.get_artist_details(self.ex_artist_id)

            self.assertIsInstance(payload['genres'], list)
            self.assertEqual(payload['id'], self.ex_artist_id)

    def test_get_playlist_by_genre_spotify(self):
            """Does searching for the spotify genre playlist work?"""

            playlist_id = spotify.get_playlist_by_genre('cowpunk', 'spotify')

            self.assertIsInstance(playlist_id, str)

    def test_get_playlist_by_genre_sounds_of_spotify(self):
            """Does searching for the 'sounds of spofity' genre playlist work?"""

            playlist_id = spotify.get_playlist_by_genre('cowpunk', 'thesoundsofspotify')

            self.assertIsInstance(playlist_id, str)

    def test_get_playlist_by_genre_not_found(self):
            """Does searching for fake genre playlist work?"""

            playlist_id = spotify.get_playlist_by_genre('post spinal tap', 'thesoundsofspotify')

            self.assertEqual(playlist_id, None)
    
    