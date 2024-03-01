# Capstone Project One | Spotify Playlist Inspector & Genre Discovery

**TITLE:** Spotify Explorer

**URL:** https://spotify-explorer.onrender.com/

![Screenshot 2024-02-19 at 3 42 01 PM](https://github.com/hatchways-community/capstone-project-one-759b191e666f4d7d93b26845cc374036/assets/22033835/788de627-75d7-4cdb-817b-d2931b281b1c)

## About the Spotify Explorer

This web app allows users to inspect data found in Spotify that they normally aren't able to view when using the Spotify app:

-   See metadata (like tempo, engery level, dancability) of tracks on a playlist
-   See which genres are associated with the tracks on a playlist
-   Jump to genre exploration pages to listen to other songs in that genre
-   Save genres as favorites or saved to review them later

This app was inspired by https://everynoise.com/

## Features

-   Inpect a playlist's tracks by submitting a (public) Spotify playlist link
-   See the artist genres and other metadata about the tracks on the playlist
-   Let user search for tracks in the playlist and let them preview the audio where Spotify has provided a preview link
-   Jump to genre exploration pages, to hear other artists in that genre
    -   Give users the option to see either Spotify's official genre playlist for that genre or "Every Noise's" Sounds of {Genre} playlist
-   Let logged in user favorite, save or dislike genres
-   Let logged in users view the genre's they've saved on their profile page
-   Let users search for genres

**Standard Flow:**

1. Go to the home page, where you will be prompted to input the link to a Spotify playlist. Clicking "Inspect!" will take you to the playlist inspector page for the playlist.
2. The playlist inpector page will show you all of the tracks of the playlist in a searchable and paginated table.
3. The table will let you prevew the songs in the list.
4. Sort the table's tracks by engery or danceability. See which genres are associated with those tracks.
5. Click a genre tag to go to the genre inpector page. By default you will see Spotify's playlist for that genre.
6. Mark the genre as 'saved' so that you remember if for later. You can go to your profile page to see your saved genres.
7. Jump to an artist page to see the artist's top tracks. Explore the track by using the track preview to see if you like the artist.

## Future Functionality

In the future, I'd like to add the following features to this app:

-   Genre index by category. This will let user explore the thousands of genres available on Spotify without finding a genre in a playlist or searching for it.
-   Genre attributes. Display metadata about a genre on the genre explore page.
-   Playlist refining. Allow users to filter for by all availabile attributes of playlist tracks.
-   Playlist creation. Allow users to create new playlists from a refinded playlist

## API Selction

Spotify Web API: https://developer.spotify.com/documentation/web-api

At this time, the app only uses client credentials, meaning the app can only access public information on Spotify. That said, this API utlizes OAuth2.0, making it possible for Spotify users to authenticate their Spotify accounts with this application, given them access to their private playlists and making it possible to create playlists for their account. In a future version, I hope to give users this ability.

## Tech Stack

The app is built using Flask and SQLAlchemy.

The following Flask extensions were leveraged: Flask-SQLA, Flask-Bcrypt (for user auth), Flask-WTF (for user forms), Jinja (HTML templates)

JavaScript is used to customize some of the styling, add audio previews, and behavior and to make certain AJAX calls to the app.

Styling and layout was done via basic Bootstrap. The playlist tables utilize the [Bootstrap-Table](https://bootstrap-table.com/) extension.

## Set Up & Run

To run this application, first ensure that your device has Python (I'm using Python 12.0) and a PostgreSQL instance that has a psql database called 'spotify_explorer'.

1. cd to the root directory
2. init and start a virtual python environment for this directory
3. install the dependencies via `pip install -r requirements. txt`
4. seed the database via `python seed.py`
5. run the app via `flask run`

To run tests:

1. Ensure that your device have a psql database called 'spotify_explorer_test'
2. At the top of the app.py file, set `TESTING` to `True` and save the file
3. Run unit test files by running commands like `python -m unittest test_spotify_client.py`
4. Once done running tests, set `TESTING` back to `False` and save the file

## DB Schema

![db diagram](https://github.com/hatchways-community/capstone-project-one-759b191e666f4d7d93b26845cc374036/assets/22033835/44221d25-0a13-452a-a136-fcffe76a0879)

_Future:_

-   **User Playlists**
    -   id (PK)
    -   user_id (FK --> users.id)
    -   playlist_id (FK --> playlists.id)
-   **Playlists**
    -   id (PK, Spotify's playlist id)
    -   created_at (datetime)
    -   updated_at (datetime)
    -   last_accessed_ad (datetime)
    -   data (cache of playlist data to avoid API request)
