from flask import Flask
from werkzeug.contrib.fixers import ProxyFix

import config


def create():
    app = Flask(__name__)
    app.config.from_object(config)

    from api_legacy import api_legacy
    from api_native import api_native
    from files import files
    from frontend import frontend
    app.register_blueprint(api_legacy, url_prefix='/api')
    app.register_blueprint(api_native)
    app.register_blueprint(files)
    app.register_blueprint(frontend)

    @app.route('/healthcheck')
    def healthcheck():
        response = app.make_response('ok')
        response.mimetype = 'text/plain'
        return response

    from db import models, database
    database.init_app(app)
    database.database.create_tables(models, safe=True)

    if config.FLASK_PROXY:
        app.wsgi_app = ProxyFix(app.wsgi_app)

    return app

if __name__ == '__main__':
    create().run(host='0.0.0.0', debug=True)
