from functools import wraps

from flask import Blueprint, abort, g, jsonify, request, url_for
from peewee import DoesNotExist

from db import User
from files import FileMapper, handle_file_upload, handle_file_delete

api_native = Blueprint('api_native', __name__, template_folder='templates')


def require_valid_api_key(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            user = User.get(User.api_key == request.form['k'])
            g.user = user
        except (KeyError, DoesNotExist):
            return jsonify(**{'status': 'not authorized'}), 403

        return f(*args, **kwargs)
    return wrap


@api_native.route('/upload', methods=['POST'])
@require_valid_api_key
def upload_file():
    file = handle_file_upload(g.user, request.files['f'])

    return jsonify(**{
        'status': 'pshuu~',
        'share_url': url_for('files.get_file',
                             name=FileMapper.b62_encode(file.id),
                             key=file.file_key,
                             _external=True),
        'delete_url': url_for('api_native.delete_file',
                              file_id=FileMapper.b62_encode(file.id),
                              key=FileMapper.get_delete_key(file.id),
                              _external=True)
    })


@api_native.route('/delete/<file_id>/<key>', methods=['GET'])
def delete_file(file_id, key):
    try:
        file_id = FileMapper.b62_decode(file_id)
        file_key = FileMapper.get_delete_key(file_id)

        if not key == file_key:
            abort(404)
    except (ValueError, DoesNotExist):
        abort(404)

    handle_file_delete(file_id)
    return jsonify(**{'status': 'pshuu~'})
