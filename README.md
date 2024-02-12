# Capstone Project One | Spotify Playlist Inspector & Genre Discovery

## API Selction

Spotify Web API: https://developer.spotify.com/documentation/web-api

This API uses OAuth2.0, making it possible for Spotify users to authenticate their Spotify accounts with this application, given them access to their private playlists and making it possible to create playlists for their account.

## DB Schema

-   **Users**
    -   id (PK)
    -   display_name (string)
-   **User Genres**
    -   id (PK)
    -   user_id (FK --> users.id)
    -   genre_id (FK --> genres.id)
    -   is_favorite (boolean)
    -   listened_to (boolean)
    -   TBD: not_interested (boolean)
-   **Genres**
    -   id (PK)
    -   title
    -   is_parent_category (boolean)
    -   is_collection (boolean)
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

_Maybe:_

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

## Guidelines

1. You will use the following technologies in this project: Python/Flask, PostgreSQL, SQLAlchemy, Heroku, Jinja, RESTful APIs, JavaScript, HTML, CSS. Depending on your idea, you might end up using WTForms and other technologies discussed in the course.
2. Every step of the project has submissions. This will alert your mentor to evaluate your work. Pay attention to the instructions so you submit the right thing. You will submit the link to your GitHub repo several times, this is for your mentor’s convenience. Your URL on GitHub is static and will not change.
3. The first two steps require mentor approval to proceed, but after that, you are free to continue working on the project after you submit your work. For instance, you don’t need your mentor to approve your database schema before you start working on your site. Likewise, you don’t need your mentor to approve the first iteration of your site before you start polishing it.
4. If you get stuck, there is a wealth of resources at your disposal. The course contains all of the material you will need to complete this project, but a well-phrased Google search might yield you an immediate solution to your problem. Don’t forget that your Slack community, TAs, and your mentor there to help you out.
5. Make sure you use a free API and deploy your project on Heroku , so everyone can see your work!
