"""Models for the Spotify Explorer app"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from flask_bcrypt import Bcrypt
from datetime import datetime

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    with app.app_context():
        db.app = app
        db.init_app(app)
        db.create_all()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    
    email = db.Column(db.Text,
                      nullable=False,
                      unique=True)

    username = db.Column(db.String(50),  # string with max len of 50 chars
                     nullable=False,
                     unique=True,)
    
    password = db.Column(db.Text,
                         nullable=False)

    image_url = db.Column(db.String(200))

    created_at = db.Column(db.DateTime,
                           nullable=False,
                           default=datetime.now())

    # SQLA relationships
    favorite_genres = db.relationship('Genre', secondary='users_genres',
                                  primaryjoin="and_(User.id==User_Genre.user_id, User_Genre.favorite_status=='favorite')",
                                  secondaryjoin="and_(User_Genre.genre_id==Genre.id, User_Genre.favorite_status=='favorite')",
                                  back_populates='favorited_by_users')

    liked_genres = db.relationship('Genre', secondary='users_genres',
                               primaryjoin="and_(User.id==User_Genre.user_id, User_Genre.favorite_status=='like')",
                               secondaryjoin="and_(User_Genre.genre_id==Genre.id, User_Genre.favorite_status=='like')",
                               back_populates='liked_by_users')

    disliked_genres = db.relationship('Genre', secondary='users_genres',
                                  primaryjoin="and_(User.id==User_Genre.user_id, User_Genre.favorite_status=='dislike')",
                                  secondaryjoin="and_(User_Genre.genre_id==Genre.id, User_Genre.favorite_status=='dislike')",
                                  back_populates='disliked_by_users')

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False
    
    def __repr__(self):
        u = self
        return f"<User id={u.id} first_name={u.username}>"
    

class Genre(db.Model):
    """A table for music genres. Columns prefixed with 'en' stand for data that came from 'everynoise.com' """
    __tablename__ = 'genres'

    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    
    title = db.Column(db.String(200),
                      nullable=False,
                      unique=True)

    # Not used at this time. May one day become a FK to a playlists table.
    spotify_playlist_id = db.Column(db.Text,
                      unique=True)

    # Not used as this time
    en_playlist_id = db.Column(db.Text,
                      unique=True)

    # Data from everynoise's analysis of Spotify genres
    en_energy_score = db.Column(db.Integer)
    en_dynamic_variation_score = db.Column(db.Integer)
    en_instrumentalness_score = db.Column(db.Integer)
    en_organic_mechanical_score = db.Column(db.Integer)
    en_dense_spiky_score = db.Column(db.Integer)
    en_popularity_score = db.Column(db.Integer)

    # SQLA relationships
    favorited_by_users = db.relationship('User', secondary='users_genres',
                                     primaryjoin="and_(Genre.id==User_Genre.genre_id, User_Genre.favorite_status=='favorite')",
                                     secondaryjoin="and_(User_Genre.user_id==User.id, User_Genre.favorite_status=='favorite')",
                                     back_populates='favorite_genres')

    liked_by_users = db.relationship('User', secondary='users_genres',
                                  primaryjoin="and_(Genre.id==User_Genre.genre_id, User_Genre.favorite_status=='like')",
                                  secondaryjoin="and_(User_Genre.user_id==User.id, User_Genre.favorite_status=='like')",
                                  back_populates='liked_genres')

    disliked_by_users = db.relationship('User', secondary='users_genres',
                                     primaryjoin="and_(Genre.id==User_Genre.genre_id, User_Genre.favorite_status=='dislike')",
                                     secondaryjoin="and_(User_Genre.user_id==User.id, User_Genre.favorite_status=='dislike')",
                                     back_populates='disliked_genres')
    
    def __repr__(self):
        return f"<Genre id={self.id} title={self.title}>"
    
class User_Genre(db.Model):
    """ A join table used to store user preferences and history with genres. """
    __tablename__ = 'users_genres'

    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)

    genre_id = db.Column(db.Integer,
                        db.ForeignKey('genres.id', ondelete='CASCADE'),
                        nullable=False)

    # Will store ENUM: favorite, like, dislike
    favorite_status = db.Column(db.String(50))
    
    last_viewed = db.Column(db.DateTime)

    # Unique constraint on the combination of user_id and genre_id
    __table_args__ = (UniqueConstraint('user_id', 'genre_id'),)
    
    def __repr__(self):
        return f"<User_Genre id={self.id} user_id={self.user_id} genre_id={self.user_id}>"
    
# Future Models to Consider:
# Genre_Category: a table used to organize genres by category so that they can easily be browsed / navigated
# Playlists: store data locally about a user's playlists that they have inspected.
# User_Playlists: join users to playlists. 
    

