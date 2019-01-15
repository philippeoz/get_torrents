from peewee import *
from .settings import DATABASE_DATA


db = PostgresqlDatabase(
    **{
        **DATABASE_DATA,
        'autocommit': True,
        'autorollback': True,
    }
)


class BaseModel(Model):
    class Meta:
        database = db


class Torrent(BaseModel):
    title = CharField(unique=True)
    date_upload = CharField(null=True)
    categories = TextField(null=True, default=None)
    cover_image = TextField(null=True, default=None)
    informations = TextField(null=True, default=None)
    synopsis = TextField(null=True, default=None)


class MagnetLink(BaseModel):
    link = TextField(null=True, default=None)
    torrent = ForeignKeyField(Torrent)
