# Capstone Project One | Spotify Playlist Inspector & Genre Discovery

**TITLE:** Spotify Explorer
**URL:** https://spotify-explorer.onrender.com/

![Screenshot 2024-02-19 at 3 42 01 PM](https://github.com/hatchways-community/capstone-project-one-759b191e666f4d7d93b26845cc374036/assets/22033835/788de627-75d7-4cdb-817b-d2931b281b1c)

## About the Spotify Explorer
This web app allows users to inspect data found in Spotify that they normally aren't able to view when using the Spotify app:
 - See metadata (like tempo, engery level, dancability) of tracks on a playlist
 - See which genres are associated with the tracks on a playlist
 - Jump to genre exploration pages to listen to other songs in that genre
 - Save genres as favorites or saved to review them later

This app was inspired by https://everynoise.com/

## Features
- Inpect a playlist's tracks by submitting a (public) Spotify playlist link
- See the artist genres and other metadata about the tracks on the playlist
- Let user search for tracks in the playlist and let them preview the audio where Spotify has provided a preview link
- Jump to genre exploration pages, to hear other artists in that genre
  - Give users the option to see either Spotify's official genre playlist for that genre or "Every Noise's" Sounds of {Genre} playlist
- Let logged in user favorite, save or dislike genres
- Let logged in users view the genre's they've saved on their profile page
- Let users search for genres

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
- Genre index by category. This will let user explore the thousands of genres available on Spotify without finding a genre in a playlist or searching for it.
- Genre attributes. Display metadata about a genre on the genre explore page.
- Playlist refining. Allow users to filter for by all availabile attributes of playlist tracks. 
- Playlist creation. Allow users to create new playlists from a refinded playlist

## API Selction

Spotify Web API: https://developer.spotify.com/documentation/web-api

At this time, the app only uses client credentials, meaning the app can only access public information on Spotify. That said, this API utlizes OAuth2.0, making it possible for Spotify users to authenticate their Spotify accounts with this application, given them access to their private playlists and making it possible to create playlists for their account. In a future version, I hope to give users this ability.

## Tech Stack
The app is built using Flask and SQLAlchemy. 

The following Flask extensions were leveraged: Flask-SQLA, Flask-Bcrypt (for user auth), Flask-WTF (for user forms), Jinja (HTML templates)

JavaScript is used to customize some of the styling, add audio previews, and behavior and to make certain AJAX calls to the app. 

Styling and layout was done via basic Bootstrap. The playlist tables utilize the [Bootstrap-Table](https://bootstrap-table.com/) extension. 

## DB Schema

-   **Users**
    -   id (PK)
    -   username (string)
    -   email (string)
    -   password (string)
    -   image_url (string)
    -   _Future:_ playlist_type_preference (string)
-   **User Genres**
    -   id (PK)
    -   user_id (FK --> users.id)
    -   genre_id (FK --> genres.id)
    -   favorite_status (ENUM: favorite, like, dislike)
    -   last_listened_to (datetime)
-   **Genres**
    -   id (PK)
    -   title
    -   spotify_playlist_id (FK --> playlists.id)
    -   en_playlist_id (FK --> playlists.id)
    -   en_energy_score (number)
    -   en_dynamic_variation_score (number)
    -   en_instrumentalness_score (number)
    -   en_organic_mechanical_score (number)
    -   en_dense_spiky_score (number)
    -   en_popularity_score (number)
-   **Genre Relationships**
    -   parent_id (PK, FK --> genres.id)
    -   child_id (PK, FK --> genres.id)

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
