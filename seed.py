"""Seed file to import genres and to make sample data for Spotify Explorer db."""

from models import db, connect_db, User, Genre, User_Genre
from enums import FavoriteStatus
from app import app
from research.genre_dict_list import genre_dict_list

# Create all tables
with app.app_context():
    db.drop_all()
    db.create_all()

    # If table isn't empty, empty it
    User.query.delete()
    Genre.query.delete()
    User_Genre.query.delete()

    # Add genres
    for genre in genre_dict_list:
        genre_record = Genre(title=genre['title'], 
                                en_energy_score=genre['energy_score'],
                                en_dynamic_variation_score=genre['dynamic_variation_score'],
                                en_instrumentalness_score=genre['instrumentalness_score'],
                                en_organic_mechanical_score=genre['organic_mechanical_score'],
                                en_dense_spiky_score=genre['dense_spiky_score'],
                                en_popularity_score=genre['popularity_score'])
        db.session.add(genre_record)

    # Add users
    condor = User.signup("Condor", "test1@example.com", "testpass")
    wayneroy = User.signup("WayneRoy", "test2@example.com", "testpass")
    ray_ray = User.signup("ray_ray", "test3@example.com", "testpass")

    db.session.commit()

    # Add user genres
    ug1 = User_Genre(user_id=condor.id, 
                        genre_id=1,
                        favorite_status=FavoriteStatus.FAVORITE)

    ug2 = User_Genre(user_id=condor.id, 
                        genre_id=2,
                        favorite_status=FavoriteStatus.SAVE)

    ug3 = User_Genre(user_id=condor.id, 
                        genre_id=3,
                        favorite_status=FavoriteStatus.DISLIKE)

    db.session.add_all([ug1, ug2, ug3])
    db.session.commit()
