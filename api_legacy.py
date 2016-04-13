import os

from flask import Blueprint, g, request, url_for
from peewee import DoesNotExist

from api_native import require_valid_api_key
from config import LEGACY_URL_HOST
from db import User, File
from files import FileMapper, handle_file_upload, handle_file_delete

api_legacy = Blueprint('api_legacy', __name__)


@api_legacy.route('/auth', methods=['POST'])
def auth():
    api_key = None
    if 'p' in request.form:
        api_key = request.form['p']
    elif 'k' in request.form:
        api_key = request.form['k']
    if api_key is None:
        return '-1'

    try:
        User.get(
            User.username == request.form['e'] and
            User.api_key == api_key)

        # Who knows what these fields mean.
        return '0,{api_key},,0'.format(
            api_key=api_key
        )
    except DoesNotExist:
        return '-1'


@api_legacy.route('/up', methods=['POST'])
@require_valid_api_key
def upload():
    file = handle_file_upload(g.user, request.files['f'])
    _, file_ext = os.path.splitext(file.original_filename)

    # Really, who knows what these fields mean.
    # Though, setting the first number to non-zero means the URL isn't
    # checked to contain puu.sh?????
    return "1,{share_host}{share_url}{file_ext},{file.id},0".format(
        share_host=LEGACY_URL_HOST,
        share_url=url_for('files.get_file',
                          name=FileMapper.b62_encode(file.id),
                          key=file.file_key),
        file_ext=file_ext,
        file=file
    )


def _generate_hist(user):
    files = (File.select()
             .where(File.user == user)
             .order_by(File.id.desc()).limit(10))

    # I have no idea what this zero means tbh.
    return '0\n' + '\n'.join((
        # I also have no idea what this last zero is.
        # The one before that is the file's view count.
        "{file.id},{file.upload_time:%Y-%m-%d %H:%M:%S},{share_url},"
        "{file.original_filename},0,0".format(
            file=file,
            share_url=url_for('files.get_file',
                              name=FileMapper.b62_encode(file.id),
                              key=file.file_key))
        for file in files
    ))


@api_legacy.route('/hist', methods=['POST'])
@require_valid_api_key
def hist():
    return _generate_hist(g.user)


@api_legacy.route('/del', methods=['POST'])
@require_valid_api_key
def delete():
    try:
        file_id = int(request.form['i'])
        delete_file = File.get(File.user == g.user and File.id == file_id)
    except ValueError:
        return '-1'
    except DoesNotExist:
        return '-2'

    if handle_file_delete(file_entry=delete_file):
        return _generate_hist(g.user)
    else:
        return '-2'
