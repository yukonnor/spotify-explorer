from flask import Flask, request, render_template, redirect, flash, session, jsonify, g
from sqlalchemy.exc import IntegrityError, NoResultFound
from functools import wraps

from forms import SignUpForm, LoginForm
from models import db, connect_db, User, Genre, User_Genre
from config import FLASK_SECRET_KEY
from spotify_client import SpotifyClient

# TODO:
# - Genre search
# - Artist page
# - Table data formatting & tool tips
# - Genre filter on table
# - Tests
#
# - User playlist type preference
# - Genre index list
# - Genre attributes display


CURR_USER_KEY = "logged_in_user"

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

    ##############################################################################
    # User signup/login/logout 

    def login_required(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not g.user:
                flash("Whoops, you need to log in to view that page.", "warning")
                return redirect("/login")  
            return view_func(*args, **kwargs)
        return wrapper


    @app.before_request
    def add_user_to_g():
        """If user is logged in, add curr user to Flask global var."""

        if CURR_USER_KEY in session:
            g.user = User.query.get(session[CURR_USER_KEY])

        else:
            g.user = None


    def do_login(user):
        """Log in user."""

        session[CURR_USER_KEY] = user.id


    def do_logout():
        """Logout user."""

        if CURR_USER_KEY in session:
            del session[CURR_USER_KEY]

    ##############################################################################
    # Login/Register/User Routes
            
    @app.route('/signup', methods=["GET", "POST"])
    def signup():
        """Handle user signup.
        Create new user and add to DB. Redirect to user profile page.
        If form not valid, present form.
        If the there already is a user with that username: flash message and re-present form.
        """

        form = SignUpForm()

        # Redirect if logged in
        if g.user:
            flash(f"You're already logged in :)", "primary")
            return redirect(f"/users/{g.user.id}")

        if form.validate_on_submit():
            try:
                user = User.signup(
                    username=form.username.data,
                    password=form.password.data,
                    email=form.email.data
                )
                db.session.commit()

            except IntegrityError:
                flash("Username or email already taken", 'danger')
                return render_template('signup.html', form=form)

            do_login(user)

            return redirect(f"/users/{user.id}")

        else:
            return render_template('signup.html', form=form)
            
    @app.route('/login', methods=["GET", "POST"])
    def login():
        """Handle user login."""
        
        # TODO: Add forgot pw flow.

        # Redirect user if already logged in.
        if g.user:
            flash(f"You're already logged in :)", "primary")
            return redirect(f"/users/{g.user.id}")

        form = LoginForm()

        if form.validate_on_submit():
            user = User.authenticate(form.username.data,
                                    form.password.data)

            if user:
                do_login(user)
                flash(f"Hello, {user.username}.", "success")
                return redirect(f"/users/{user.id}")

            flash("Invalid username/password...", 'danger')
            return render_template('login.html', form=form)

        return render_template('login.html', form=form)


    @app.route('/logout')
    @login_required
    def logout():
        """Handle logout of user."""

        do_logout()

        flash("You've been logged out. See ya later.", 'primary')
        return redirect("/")
    
    @app.route('/users/<int:user_id>')
    @login_required
    def show_profile(user_id):
        """Show the user's profile page.
           At this time, users can only see their own profile page."""
        
        if g.user and session[CURR_USER_KEY] != user_id:
            flash("Sorry. You can only view your own profile at this time.", "warning")
            return redirect(f"/users/{session[CURR_USER_KEY]}")

        user = User.query.get_or_404(user_id)
        favorite_genres = user.favorite_genres
        saved_genres = user.saved_genres
        disliked_genres = user.disliked_genres
        
        return render_template('profile.html', user=user, favorite_genres=favorite_genres, saved_genres=saved_genres, disliked_genres=disliked_genres)

    ##############################################################################
    # General Routes

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

    @app.route('/search-genre')
    def search_genre():
        """Process the 'search genre' form, redirecting user to the genre inspector page for the genre."""

        genre_title = request.args.get('genre')
        genre_title = genre_title.lower()

        genre_title_wildcards = genre_title.replace(' ', '%')

        # See if genre in db
        try:
            genre = Genre.query.filter(Genre.title.like(genre_title_wildcards)).first()
        except NoResultFound:
            flash("Gah, sorry. I couldn't find that genre in Spotify's genre list.", 'warning')
            return redirect('/genres')    

        return redirect(f'/genre-inspector/{genre.title}')

    @app.route('/genre-inspector/<genre_title>')
    def genre_inspector(genre_title):

        # See if genre in db
        try:
            genre = Genre.query.filter(Genre.title == genre_title).one()
        except NoResultFound:
                flash("Gah, sorry. I couldn't find that genre in Spotify's genre list.", 'warning')
                return redirect('/genres')    
        
        # If user logged in, get genre favorite status last time user viewed genre:
        if g.user:
            last_viewed, favorite_status = User_Genre.get_user_genre_facts(genre, g.user.id)
        else:
            last_viewed = None
            favorite_status = None

        # Get playlist source (owner type) from query string
        source = request.args.get('source')

        if source == 'spotify' or source == 'thesoundsofspotify':
            playlist_id =spotify.get_playlist_by_genre(genre_title, source)
        elif source is None:
            playlist_id =spotify.get_playlist_by_genre(genre_title, 'spotify')
        else: 
            flash("I don't currently support the type of playlist you were looking for.", "warning")
            return redirect('/')

        playlist_info_payload = spotify.get_playlist_info(playlist_id)

        if not playlist_info_payload:
            # Question: What is a better way to handle this? How can I get status code (or other error details) from get_playlist_info() to include in flash message?
            flash("Wasn't able to fetch the playlist :/  (Devs: see logs for details)", "warning")  
            return redirect('/')
        
        playlist_link = f'https://open.spotify.com/playlist/{playlist_id}'

        return render_template('genre-inspector.html', genre=genre, source=source, playlist=playlist_info_payload, playlist_link=playlist_link, last_viewed=last_viewed, favorite_status=favorite_status)

    @app.route('/users/update-genre-favorite-status', methods=["POST"])
    @login_required
    def update_genre_favorite_status():
        """ Process AJAX request to set user's favorite status for a genre """

        try:
            # Parse JSON data from the request
            data = request.get_json()

            # Access individual fields from the JSON data
            genre_id = data.get('genre_id')
            favorite_status = data.get('favorite_status')

            # Get and update user_genre record
            user_genre = User_Genre.query.filter(User_Genre.user_id == g.user.id, User_Genre.genre_id == genre_id).first()

            user_genre.favorite_status = favorite_status
            db.session.commit()

            # Assuming success, return a JSON response
            return jsonify({'message': 'Update successful'})

        except Exception as e:
            # Handle exceptions or errors here
            return jsonify({'error': str(e)}), 500
        
    @app.route('/artists/<artist_id>')
    def show_artist(artist_id):
        """Render the artist page. At this point, it just shows the artist's top tracks."""

        artist_payload = spotify.get_artist_details(artist_id)

        if not artist_payload:
            flash("Wasn't able to fetch the artist :/  (Devs: see logs for details)", "warning")
            return redirect('/')

        return render_template('artist-detail.html', artist=artist_payload)
    
    @app.route('/artists/<artist_id>/top-tracks')
    def get_artist_top_tracks(artist_id):
        """Fetch the artist's top tracks via bootstrap-table AJAX call."""

        top_tracks_payload = spotify.get_artist_top_tracks(artist_id)

        # Create a JSON response
        response = jsonify(top_tracks_payload)

        # Add Cache-Control header to force caching for 3 hours
        response.headers['Cache-Control'] = 'max-age=10600'

        return response

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
    # app.app_context().push() # remove when done testing
    connect_db(app)
    app.run(debug=False)      