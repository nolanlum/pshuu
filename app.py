from flask import Flask
from werkzeug.contrib.fixers import ProxyFix

import config


def add_user():
    username = input('Username: ')
    api_key = input('API Key: ')

    create()

    from db import User
    User().create(username=username, api_key=api_key).save()


def create():
    app = Flask(__name__)
    app.config.from_object(config)

    from api_native import api_native
    from files import files
    app.register_blueprint(api_native)
    app.register_blueprint(files)

    from db import models, database
    database.init_app(app)
    database.database.create_tables(models, safe=True)

    if config.FLASK_PROXY:
        app.wsgi_app = ProxyFix(app.wsgi_app)

    return app

if __name__ == '__main__':
    # add_user()
    create().run(host='0.0.0.0', debug=True)
