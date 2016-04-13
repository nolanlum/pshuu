import datetime

from peewee import CharField, ForeignKeyField, DateTimeField
from playhouse.flask_utils import FlaskDB

database = FlaskDB()


class User(database.Model):
    username = CharField(unique=True)
    api_key = CharField(unique=True)


class File(database.Model):
    user = ForeignKeyField(User)
    original_filename = CharField()
    file_key = CharField(null=True)
    content_type = CharField(null=True)
    upload_time = DateTimeField(default=datetime.datetime.now)

models = [User, File]
