from peewee import CharField, ForeignKeyField
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

models = [User, File]
