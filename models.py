"""Models for the Spotify Explorer app"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, Enum
from sqlalchemy.orm.exc import NoResultFound
from flask_bcrypt import Bcrypt
from datetime import datetime

from enums import FavoriteStatus

bcrypt = Bcrypt()

# Set expire_on_commit to False to support unit tests
db = SQLAlchemy(session_options={"expire_on_commit": False})

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
    user_genres = db.relationship('User_Genre', backref='user')
                            #  back_populates='users')

    def favorite_genres(self):
        """Return list of Genre objects for genre's that this user has favorited."""
        return [ug.genre for ug in self.user_genres if ug.favorite_status == FavoriteStatus.FAVORITE]

    def saved_genres(self):
        """Return list of Genre objects for genre's that this user has saved."""
        return [ug.genre for ug in self.user_genres if ug.favorite_status == FavoriteStatus.SAVE]

    def disliked_genres(self):
        """Return list of Genre objects for genre's that this user has disliked."""
        return [ug.genre for ug in self.user_genres if ug.favorite_status == FavoriteStatus.DISLIKE]

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username.lower(),
            email=email,
            password=hashed_pwd
        )

        db.session.add(user)
        db.session.commit()

        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), raise an error noting
        whether the user couln't be found or password incorrect.
        """

        try:
            user = cls.query.filter_by(username=username.lower()).one()
        except NoResultFound:
            raise NoResultFound("User not found with the provided username")

        authenticated = bcrypt.check_password_hash(user.password, password)
        
        if not authenticated:
            raise ValueError("Incorrect password")

        return user
    
    def __repr__(self):
        u = self
        return f"<User id={u.id}: {u.username}, {u.email}>"
    

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
    user_genres = db.relationship('User_Genre', backref='genre')

    def favorited_by_users(self):
        """Return users that marked this genres as 'favorite'"""
        return [ug.user for ug in self.user_genres if ug.favorite_status == FavoriteStatus.FAVORITE]

    def saved_by_users(self):
        """Return users that marked this genres as 'saved'"""
        return [ug.user for ug in self.user_genres if ug.favorite_status == FavoriteStatus.SAVE]

    def disliked_by_users(self):
        """Return users that marked this genres as 'disliked'"""
        return [ug.user for ug in self.user_genres if ug.favorite_status == FavoriteStatus.DISLIKE]

    
    @classmethod
    def lookup_genre(cls, genre_title):
        """See if genre is in the genre table. If so, return it. Otherwise return None."""
        # Parse genre to sql search string with wildcards
        genre_title = genre_title.lower()
        genre_title_wildcards = genre_title.replace(' ', '%')

        return Genre.query.filter(Genre.title.like(genre_title_wildcards)).first() 
   
   
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

    favorite_status = db.Column(Enum(FavoriteStatus), nullable=True)
    
    last_viewed = db.Column(db.DateTime,
                            nullable=False,
                            default=datetime.now())

    # Unique constraint on the combination of user_id and genre_id
    __table_args__ = (UniqueConstraint('user_id', 'genre_id'),)
    
    def __repr__(self):
        return f"<User_Genre id={self.id} user_id={self.user_id} genre_id={self.user_id}>"
    

    @classmethod
    def update_user_genre_fav_status(cls, user_id, genre_id, favorite_status_enum):
        """Get and update a user's favorite status for a genre."""

        try:
            user_genre = cls.query.filter(cls.user_id == user_id, cls.genre_id == genre_id).one()
        except NoResultFound:
            raise NoResultFound("User doesn't have relationship to genre.")
        
        user_genre.favorite_status = favorite_status_enum
        db.session.commit()
    
    @classmethod
    def get_user_genre_facts(cls, genre, user_id):
        """Get the last_view date or string and the favorite status for a user and genre."""

        user_genre = cls.query.filter(cls.user_id == user_id, cls.genre_id == genre.id).first()
            
        if user_genre:
            if user_genre.last_viewed:
                last_viewed = user_genre.last_viewed.date()
            else:
                last_viewed = "First time! (while logged in)"

            if user_genre.favorite_status:
                favorite_status = user_genre.favorite_status
            else:
                favorite_status = None

            # update the last viewed datetime
            user_genre.update_last_viewed()
        
        # Create user_genre record
        else:
            user_genre = User_Genre(user_id=user_id, genre_id=genre.id)
            db.session.add(user_genre)
            db.session.commit()

            last_viewed = "First time! (while logged in)" # still show init message
            favorite_status = None

        return last_viewed, favorite_status
    
    def update_last_viewed(self):
        self.last_viewed = datetime.now()
        db.session.commit()

    