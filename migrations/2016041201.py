import datetime

from playhouse.migrate import *

from config import DATABASE

migrator = SqliteMigrator(SqliteDatabase(DATABASE['name']))

upload_time = DateTimeField(default=datetime.datetime.now)

migrate(
    migrator.add_column('file', 'upload_time', upload_time)
)