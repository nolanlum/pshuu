import os
from functools import wraps

from flask import Blueprint, abort, g, jsonify, request, url_for
from peewee import DoesNotExist

from config import UPLOAD_HOST
from db import File, User
from files import FileMapper

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
    file_mapper = FileMapper(g.user)

    # Ensure file was uploaded.
    file = request.files['f']
    if not file:
        abort(400)

    # Get ID for file.
    file_entry = File().create(
        user=g.user,
        original_filename=file.filename,
        content_type=file.content_type or None)
    file_entry.save()

    # Generate file key based on username and ID and update record.
    file_id = file_entry.id
    file_key = file_mapper.get_file_key(file_id)
    file_entry.file_key = file_key
    file_entry.save()

    # Ensure path to save exists and save file.
    storage_path = file_mapper.get_storage_path(file_id)
    storage_dir = os.path.dirname(storage_path)
    if not os.path.exists(storage_dir):
        try:
            os.makedirs(storage_dir)
        except OSError:
            if not os.path.exists(storage_dir):
                raise
    file.save(storage_path)

    return jsonify(**{
        'status': 'pshuu~',
        'share_url': UPLOAD_HOST + url_for('files.get_file',
                                           name=file_mapper.b62_encode(file_id),
                                           key=file_key),
        'delete_url': ''
    })
