from flask import Flask, request, render_template, redirect, flash, session, jsonify
from models import db, connect_db, User, Genre, User_Genre
from config import FLASK_SECRET_KEY
from spotify_client import SpotifyClient

def create_app(db_name, testing=False, developing=False):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = FLASK_SECRET_KEY
    app.testing = testing
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql:///{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']  =  False

    if developing: 
        app.config['SQLALCHEMY_ECHO'] =  True
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

    spotify = SpotifyClient()

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
        """Render the playlist inspector page. The track data used to populate the playlist tracks data will be a separate AJAX request."""

        playlist_info_payload = spotify.get_playlist_info(playlist_id)

        if not playlist_info_payload:
            flash("Wasn't able to fetch the playlist :/  (Devs: see logs for details)", "warning")
            return redirect('/')
        
        # set playlist link
        playlist_link = f'https://open.spotify.com/playlist/{playlist_id}'

        # TODO: show a genre count table (maybe broken down by parent genre vs specific genre)

        return render_template('playlist-inspector.html', playlist=playlist_info_payload, playlist_link=playlist_link)

    @app.route('/get-playlist-tracks/<playlist_id>')
    def playlist_tracks(playlist_id):
        """Provide playlist track data to the bootstrap-table's AJAX request."""

        tracks = spotify.get_playlist_tracks(playlist_id)

        # Create a JSON response
        response = jsonify(tracks)

        # Add Cache-Control header to force caching for 3 hours
        response.headers['Cache-Control'] = 'max-age=10600'

        return response


    @app.route('/genre-inspector/<genre_title>')
    def genre_inspector(genre_title):

        print(f"Generating genre inspector page for {genre_title}...")

        # Get playlist source (owner type) from query string
        source = request.args.get('source')

        if source == 'spotify' or source == 'thesoundsofspotify':
            playlist_id =spotify.get_playlist_by_genre(genre_title, source)
        else: 
            flash("I don't currently support the type of playlist you were looking for.", "warning")
            return redirect('/')

        playlist_info_payload = spotify.get_playlist_info(playlist_id)

        if not playlist_info_payload:
            # Question: What is a better way to handle this? How can I get status code (or other error details) from get_playlist_info() to include in flash message?
            flash("Wasn't able to fetch the playlist :/  (Devs: see logs for details)", "warning")  
            return redirect('/')
        
        playlist_link = f'https://open.spotify.com/playlist/{playlist_id}'

        return render_template('genre-inspector.html', genre_title=genre_title, source=source, playlist=playlist_info_payload, playlist_link=playlist_link)

    return app

# Misc Functions ################################################

def extract_playlist_id(link):
    parts = link.split('/')

    # Find the index of 'playlist' in the parts list
    playlist_index = parts.index('playlist')

    # Extract the playlist ID from the next part
    playlist_id = parts[playlist_index + 1].split('?')[0]

    return playlist_id



# Run ################################################

if __name__ == "__main__":
    app = create_app('spotify_explorer', developing=True)
    app.app_context().push() # remove when done testing
    connect_db(app)
    app.run(debug=True)      # show when done testing