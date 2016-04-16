import os
from functools import wraps

from flask import Blueprint, abort, g, jsonify, request, url_for
from peewee import DoesNotExist

from db import File, User
from files import FileMapper
from files import handle_file_upload, handle_file_delete, url_for_file

api_native = Blueprint('api_native', __name__)


def require_valid_api_key(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            user = User.get(User.api_key == request.form['k'])
            g.user = user
        except (KeyError, DoesNotExist):
            return jsonify(status='not authorized'), 403

        return f(*args, **kwargs)
    return wrap


@api_native.route('/upload', methods=['POST'])
@require_valid_api_key
def upload_file():
    file = handle_file_upload(g.user, request.files['f'])
    _, file_ext = os.path.splitext(file.original_filename)

    return jsonify(
        status='pshuu~',
        share_url=url_for_file(file),
        delete_url=url_for('api_native.delete_file',
                           file_id=FileMapper.b62_encode(file.id),
                           key=FileMapper.get_delete_key(file.id),
                           _external=True))


@api_native.route('/delete/<file_id>/<key>', methods=['GET'])
def delete_file(file_id, key):
    try:
        file_id = FileMapper.b62_decode(file_id)
        file_key = FileMapper.get_delete_key(file_id)

        if not key == file_key:
            abort(404)
    except (ValueError, DoesNotExist):
        abort(404)

    if handle_file_delete(file_id=file_id):
        return jsonify(status='pshuu~')
    else:
        abort(404)


@api_native.route('/list', methods=['GET', 'POST'])
def list_files():
    putative_key = request.args.get('k') or request.form.get('k')
    try:
        user = User.get(User.api_key == putative_key)
    except DoesNotExist:
        user = None

    if user is None:
        return jsonify(status='not authorized'), 403
    else:
        return jsonify(
            status='pshuu~',
            files={
                f.id: {'original_filename': f.original_filename,
                       'upload_time': f.upload_time,
                       'url': url_for_file(f)
                       }
                for f in File.select().where(File.user == user)})
