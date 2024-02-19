from unittest import TestCase

from app import create_app, CURR_USER_KEY, g
from models import db, connect_db, User, Genre, User_Genre


app = create_app("spotify_explorer_test", testing=True)
app.config['WTF_CSRF_ENABLED'] = False
connect_db(app)

with app.app_context():
    db.drop_all()
    db.create_all()


class SpotifyExplorerViewTests(TestCase):
    """Tests for the Spotify Explorer views."""

    def setUp(self):
         with app.app_context():
            
            # Delete all data in the tables to start fresh.
            db.session.rollback()
            User.query.delete()
            Genre.query.delete()
            User_Genre.query.delete()

            # Seed test db
            u1 = User.signup("u1", "test1@example.com", "testpass1")
            u2 = User.signup("u2", "test2@example.com", "testpass2")

            genre_1 = Genre(title='pop', 
                             en_energy_score=500,
                             en_dynamic_variation_score=500,
                             en_instrumentalness_score=500,
                             en_organic_mechanical_score=500,
                             en_dense_spiky_score=500,
                             en_popularity_score=500)
            
            genre_2 = Genre(title='rock', 
                             en_energy_score=400,
                             en_dynamic_variation_score=400,
                             en_instrumentalness_score=400,
                             en_organic_mechanical_score=400,
                             en_dense_spiky_score=400,
                             en_popularity_score=400)
            
            genre_3 = Genre(title='cowpunk', 
                             en_energy_score=300,
                             en_dynamic_variation_score=300,
                             en_instrumentalness_score=300,
                             en_organic_mechanical_score=300,
                             en_dense_spiky_score=300,
                             en_popularity_score=300)

            db.session.add_all([genre_1, genre_2, genre_3])
            db.session.commit()

            ug1 = User_Genre(user_id=u1.id, 
                            genre_id=genre_1.id,
                            favorite_status='favorite')
            
            ug2 = User_Genre(user_id=u1.id, 
                            genre_id=genre_2.id,
                            favorite_status='favorite')
            
            ug3 = User_Genre(user_id=u2.id, 
                            genre_id=genre_1.id,
                            favorite_status='save')
            
            ug4 = User_Genre(user_id=u2.id, 
                            genre_id=genre_2.id,
                            favorite_status='dislike')
            
            ug5 = User_Genre(user_id=u1.id, 
                            genre_id=genre_3.id)

            db.session.add_all([ug1, ug2, ug3, ug4, ug5])
            db.session.commit()

            self.client = app.test_client()
            self.context = app.app_context()
            self.u1 = u1
            self.u2 = u2
            self.genre_1 = genre_1
            self.genre_2 = genre_2
            self.genre_3 = genre_3
            self.ex_artist_id = "3u1ulLq00Y3bfmq9FfjsPu"
            self.ex_short_playlist_id = "37i9dQZF1EIgtiaACXv6tQ"
            self.ex_long_playlist_id = "6VbtVCyMUz0eoiWGl2r6g7"
            self.ex_track_id = "7cGwqXXVav9Tg0XNoONPlo"

    def tearDown(self):
        """Clean up any fouled transaction."""

        with app.app_context():
            db.session.rollback()

    def test_home(self):
        """Test whether home page loads"""
        with app.test_client() as client:
            resp = client.get("/")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Playlist Inspector</h1>', html)
    
    def test_nav_logged_out(self):
        """Test whether home page loads"""
        with app.test_client() as client:
            resp = client.get("/")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('href="/login">Log In</a></li>', html)

    def test_nav_logged_in(self):
        """Test whether home page loads"""
        with app.test_client() as client:

            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1.id
  
            resp = client.get("/")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('href="/logout">Log out</a></li>', html)

    def test_user_signup(self):
        """Can a user signup?"""

        with self.client as c:

            resp = c.post("/signup", data={"username": "random_user", "password": "testpass", "email":"random@test.com"})

            html = resp.get_data(as_text=True)

            print(html)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            # Find the user and see if username matches
            new_user = User.query.filter(User.username == 'random_user').one()
            self.assertEqual(new_user.email, "random@test.com")

    def test_user_signup_fail(self):
        """Can a user signup if they provide a duplicate username?"""

        with self.client as c:

            resp = c.post("/signup", data={"username": "u1", "password": "testpass", "email":"random@test.com"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username or email already taken", html)

    def test_user_login_success(self):
        """Can a user log in?"""

        with self.client as c:

            resp = c.post("/login", data={"username": self.u1.username, "password": "testpass1"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make request is successful and username in success alert
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"Hello, {self.u1.username}", html)

    def test_user_login_fail(self):
        """Does login fail if password is incorrect?"""

        with self.client as c:

            resp = c.post("/login", data={"username": self.u1.username, "password": "wrongpass"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make request is successful and username in success alert
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid username/password...", html)

    def test_user_logout(self):
        """Does logout work?"""

        with self.client as c:

            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1.id

            resp = c.get("/logout", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("You&#39;ve been logged out. See ya later", html)

            with c.session_transaction() as session:
                self.assertEqual(session.get(CURR_USER_KEY), None)

    def test_user_profile(self):
        """Can a user see their own profile page when logged in?"""

        with self.client as c:

            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1.id

            resp = c.get(f"/users/{self.u1.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<h1 class="display-4">{self.u1.username}</h1>', html)

    def test_user_profile_logged_out(self):
        """Can a user a profile page when logged out?"""

        with self.client as c:

            resp = c.get(f"/users/{self.u1.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Whoops, you need to log in to view that page.', html)

    def test_other_user_profile(self):
        """Can a user see a different user's profile page when logged in?"""

        with self.client as c:

            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1.id

            resp = c.get(f"/users/{self.u2.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sorry. You can only view your own profile at this time.', html)

    def test_user_profile_fav_genre(self):
        """Can a user see their favorite genre(s) on their profile page when logged in?"""

        with self.client as c:

            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1.id

            resp = c.get(f"/users/{self.u1.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<span class="genre badge rounded-pill text-bg-warning mr-1">{self.genre_1.title}</span>', html)

    def test_genre_index(self):
        """Test whether genre index page loads"""

        with app.test_client() as client:
            resp = client.get("/genres")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Genres by Category', html)

    def test_genre_search(self):
        """Test whether genre page loads when a search is performed"""

        with app.test_client() as client:
            query = {"genre": "Cow Punk"}  # also testing that search removes the space as well (actual genre is "cowpunk")
            resp = client.get("/search-genre", query_string=query, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h1 class="display-4">Cowpunk Mix</h1>', html)
            self.assertIn("table-responsive", html)

    def test_genre_inspector(self):
        """Test whether the genre inspector page loads"""

        with app.test_client() as client:
            resp = client.get("/genre-inspector/cowpunk?source=spotify")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h1 class="display-4">Cowpunk Mix</h1>', html)
            self.assertIn('<a href="/genre-inspector/cowpunk?source=thesoundsofspotify">', html)

    def test_playlist_search(self):
        """Test whether a playlist page loads when a search is performed"""

        with app.test_client() as client:
            query = {"playlistLink": "https://open.spotify.com/playlist/37i9dQZF1EIgtiaACXv6tQ?si=a465d3aa48404754"} 
            resp = client.get("/get-playlist", query_string=query, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h1 class="display-4">Cowpunk Mix</h1>', html)
            self.assertIn("table-responsive", html)

    def test_playlist_inspector(self):
        """Test whether a playlist page loads"""

        with app.test_client() as client:
            resp = client.get(f"/playlist-inspector/{self.ex_short_playlist_id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h1 class="display-4">Cowpunk Mix</h1>', html)
            self.assertIn("table-responsive", html)

    def test_artist_page(self):
        """Test whether a artist page loads"""

        with app.test_client() as client:
            resp = client.get(f"/artists/{self.ex_artist_id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h1 class="display-4">Ween</h1>', html)
            self.assertIn("table-responsive", html)

    # Test AJAX Call Responses
            
    def test_get_artist_top_tracks(self):
        """Test whether the artist top tracks AJAX call responds with data"""

        with app.test_client() as client:
            resp = client.get(f"/artists/{self.ex_artist_id}/top-tracks")
            
            self.assertEqual(len(resp.json),10)
            self.assertEqual(resp.json[0]['artists'][0]['name'],"Ween")

    def test_playlist_tracks(self):
        """Test whether the playlist tracks AJAX call responds with data"""

        with app.test_client() as client:
            resp = client.get(f"/get-playlist-tracks/{self.ex_short_playlist_id}")
            
            self.assertEqual(len(resp.json),50)
            self.assertIn("cowpunk",resp.json[0]['artist_genres'])


    def test_update_genre_favorite_status(self): 
        """Test whether updating user genre preference works."""

        with app.test_client() as c:

            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1.id

            resp = c.post("/users/update-genre-favorite-status", json={"genre_id": f"{self.genre_3.id}", "favorite_status": "favorite"})

            self.assertEqual('Update successful', resp.json['message'])
    
            






            


    