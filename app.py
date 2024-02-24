from flask import Flask, request, render_template, redirect, flash, session, jsonify, g
from sqlalchemy.exc import IntegrityError, NoResultFound
from functools import wraps

from forms import SignUpForm, LoginForm
from models import db, connect_db, User, Genre, User_Genre
from config import FLASK_SECRET_KEY, SQLALCHEMY_DATABASE_URI_PROD
from spotify_client import SpotifyClient

# TODO:
# - Genre filter on table
# - User playlist type preference
# - Genre index list
# - Genre attributes display

TESTING = False   # Set True here if you are running tests
CURR_USER_KEY = "logged_in_user"

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI_PROD
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']  =  False

# Development helpters
app.testing = False
app.config['SQLALCHEMY_ECHO'] =  False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

if TESTING: 
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///spotify_explorer_test'
    app.app_context().push() 
    app.testing = True

connect_db(app) 

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

        try:
            user = User.authenticate(form.username.data, form.password.data)      
      
        except NoResultFound as e:
            print(f"Error: {e}")
            flash("Couldn't find an account with that username...", 'danger')
            return render_template('login.html', form=form)
        
        except ValueError as e:
            print(f"Error: {e}")
            flash("Invalid username/password...", 'danger')
            return render_template('login.html', form=form)

        # if user not found, exception will be raised, so it is safe to log in user:
        do_login(user)
        flash(f"Hello, {user.username}.", "success")
        return redirect(f"/users/{user.id}")        

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

    # See if genre in db
    genre = Genre.lookup_genre(genre_title)
    
    if genre:
        return redirect(f'/genre-inspector/{genre.title}')
    else:
        flash("Gah, sorry. I couldn't find that genre in Spotify's genre list.", 'warning')
        return redirect('/genres')  

@app.route('/genre-inspector/<genre_title>')
def genre_inspector(genre_title):

    # See if genre in db
    genre = Genre.lookup_genre(genre_title)
    
    if not genre:
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
        playlist_id = spotify.get_playlist_by_genre(genre.title, source)
        alt_source = 'thesoundsofspotify' if source == 'spotify' else 'spotify'
    elif source is None:
        source = 'spotify'
        playlist_id = spotify.get_playlist_by_genre(genre.title, source)
        alt_source = 'thesoundsofspotify'
    else: 
        flash("I don't currently support the type of playlist you were looking for.", "warning")
        return redirect('/')

    playlist_info_payload = spotify.get_playlist_info(playlist_id)

    if not playlist_info_payload:
        flash(f"""Wasn't able to find {source.title()}'s playlist for that genre :/  Try looking for <a href="/genre-inspector/{genre.title}?source={alt_source}">{alt_source.title()}'s version</a>.""", "warning")  
        return redirect(request.referrer or '/')
    
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

        # Update user_genre record
        User_Genre.update_user_genre_fav_status(g.user.id, genre_id, favorite_status)

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

# Misc Functions ################################################

def extract_playlist_id(link):
    parts = link.split('/')

    # Find the index of 'playlist' in the parts list
    playlist_index = parts.index('playlist')

    # Extract the playlist ID from the next part
    playlist_id = parts[playlist_index + 1].split('?')[0]

    return playlist_id
