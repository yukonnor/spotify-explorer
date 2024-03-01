from enum import Enum

class FavoriteStatus(Enum):
    FAVORITE = 'favorite'
    SAVE = 'save'
    DISLIKE = 'dislike'

FAVORITE_STATUS_MAP = {
    "favorite": FavoriteStatus.FAVORITE,
    "save": FavoriteStatus.SAVE,
    "dislike": FavoriteStatus.DISLIKE,
}