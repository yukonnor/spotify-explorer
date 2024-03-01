from unittest import TestCase

from app import app, db, TESTING
from models import db, User, Genre, User_Genre
from enums import FavoriteStatus
from sqlalchemy.exc import IntegrityError, NoResultFound

if TESTING: 
    
    db.drop_all()
    db.create_all()


    class SpotifyExplorerModelTests(TestCase):
        """Tests for the Spotify Explorer data model."""

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

                db.session.add_all([genre_1, genre_2])
                db.session.commit()

                ug1 = User_Genre(user_id=u1.id, 
                                genre_id=genre_1.id,
                                favorite_status=FavoriteStatus.FAVORITE)
                
                ug2 = User_Genre(user_id=u1.id, 
                                genre_id=genre_2.id,
                                favorite_status=FavoriteStatus.FAVORITE)
                
                ug3 = User_Genre(user_id=u2.id, 
                                genre_id=genre_1.id,
                                favorite_status=FavoriteStatus.SAVE)
                
                ug4 = User_Genre(user_id=u2.id, 
                                genre_id=genre_2.id,
                                favorite_status=FavoriteStatus.DISLIKE)

                db.session.add_all([ug1, ug2, ug3, ug4])
                db.session.commit()

                self.client = app.test_client()
                self.context = app.app_context()
                self.u1 = u1
                self.u2 = u2
                self.genre_1 = genre_1
                self.genre_2 = genre_2
                self.ug1 = ug1
                self.ug2 = ug2

        def tearDown(self):
            """Clean up any fouled transaction."""

            with app.app_context():
                db.session.rollback()

        def test_user_repr(self):
            """Does the repr of user objects work as expected?"""
            with app.app_context():
                self.assertEqual(repr(self.u1), f"<User id={self.u1.id}: {self.u1.username}, {self.u1.email}>")
        
        def test_genre_repr(self):
            """Does the repr of genre objects work as expected?"""
            with app.app_context():
                genre = self.genre_1
                self.assertEqual(repr(genre), f"<Genre id={genre.id} title={genre.title}>")

        def test_user_genre_repr(self):
            """Does the repr of user genre objects work as expected?"""
            with app.app_context():
                user_genre = self.ug1
                self.assertEqual(repr(user_genre), f"<User_Genre id={user_genre.id} user_id={user_genre.user_id} genre_id={user_genre.user_id}>")

        def test_user_model(self):
            """Does basic user model work?"""
            with app.app_context():
                u = User(
                    email="test@test.com",
                    username="testuser",
                    password="HASHED_PASSWORD"
                )

                db.session.add(u)
                db.session.commit()

                # User should have no genre relationships
                self.assertEqual(len(u.favorite_genres()), 0)
                self.assertEqual(len(u.saved_genres()), 0)
                self.assertEqual(len(u.disliked_genres()), 0)

                # User record should have matching username
                user = User.query.get(u.id)
                self.assertEqual(user.username, "testuser")

        def test_user_signup(self):
            """Does user sign up work?"""
            with app.app_context():
                user = User.signup("u100", "test100@example.com", "testpass100")
                db.session.commit()

                # User record should have matching username
                user = User.query.get(user.id)
                self.assertEqual(user.username, "u100")

        def test_user_signup_fail_dupe_username(self):
            """Does user sign up fail if dupe username used?"""
            with app.app_context():

                # Registering new user with matching username should result in error
                with self.assertRaises(IntegrityError) as context:
                    user = User.signup("u1", "test100@example.com", "testpass100")
                    db.session.commit()
                    

                self.assertIn('duplicate key value violates unique constraint "users_username_key"', str(context.exception))

        def test_user_signup_fail_dupe_email(self):
            """Does user sign up fail if dupe email used?"""
            with app.app_context():

                # Registering new user with matching username should result in error
                with self.assertRaises(IntegrityError) as context:
                    user = User.signup("new_user", "test1@example.com", "testpass100")
                    db.session.commit()
                    

                self.assertIn('duplicate key value violates unique constraint "users_email_key"', str(context.exception))

        def test_user_authentication(self):
            """Does user authentication work?"""
            with app.app_context():
                user = User.authenticate("u1", "testpass1")

                # Matching user record should be returned
                self.assertEqual(user.id, self.u1.id)

        def test_user_authentication_fails_pw(self):
            """Does user authentication fail if wrong password provided?"""
            with app.app_context():
                with self.assertRaises(ValueError) as context:
                    User.authenticate("u1", "asdfasdfasdf")

                self.assertEqual(str(context.exception), "Incorrect password")

        def test_user_authentication_fails_username(self):
            """Does user authentication fail if non-existant username provided?"""
            with app.app_context():
                with self.assertRaises(NoResultFound) as context:
                    User.authenticate("u99999", "asdfasdfasdf")

                self.assertEqual(str(context.exception), "User not found with the provided username")

        def test_user_genre_relationship(self):
            """Does the User User_Genre relationship work?"""
            with app.app_context():
                user = User.query.filter_by(id=self.u1.id).first()

                # Access the relationship
                user_genres = user.user_genres
                
                self.assertEqual(len(user_genres), 2)

        def test_user_favorite_status_methods(self):
            """Do the user genre favorite status methods work?"""
            with app.app_context():
                user = User.query.filter_by(id=self.u1.id).first()

                favorite_genres = user.favorite_genres()
                saved_genres = user.saved_genres()
                disliked_genres = user.disliked_genres()


                self.assertEqual(len(favorite_genres), 2)
                self.assertEqual(len(saved_genres), 0)
                self.assertEqual(len(disliked_genres), 0)

                self.assertEqual(favorite_genres[0].title, 'pop')

        def test_genre_user_relationship(self):
            """Does the genre user_genres relationships work?"""
            with app.app_context():

                pop = Genre.query.filter_by(id=self.genre_1.id).first()

                # Access the relationship
                user_genres = pop.user_genres
                
                self.assertEqual(len(user_genres), 2)

        def test_genre_user_favorite_status_methods(self):
            """Do user favorited_by_users / saved_by_users / disliked_by_users methods work?"""
            with app.app_context():
                pop = Genre.query.filter_by(id=self.genre_1.id).first()
                rock = Genre.query.filter_by(id=self.genre_2.id).first()

                # Access the relationships
                pop_favorited_by_users = pop.favorited_by_users()
                pop_saved_by_users = pop.saved_by_users()
                pop_disliked_by_users = pop.disliked_by_users()
                rock_favorited_by_users = rock.favorited_by_users()
                rock_saved_by_users = rock.saved_by_users()
                rock_disliked_by_users = rock.disliked_by_users()
                
                self.assertEqual(len(pop_favorited_by_users), 1)
                self.assertEqual(len(pop_saved_by_users), 1)
                self.assertEqual(len(pop_disliked_by_users), 0)

                self.assertEqual(len(rock_favorited_by_users), 1)
                self.assertEqual(len(rock_saved_by_users), 0)
                self.assertEqual(len(rock_disliked_by_users), 1)

else:
    print("Be sure to set TESTING to True in the app.py file.")