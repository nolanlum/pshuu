from functools import lru_cache

import hashlib
import hmac
import os
from base64 import urlsafe_b64encode
from urllib.parse import quote

from flask import Blueprint, abort, send_file, url_for
from peewee import DoesNotExist

from config import UPLOAD_DIRECTORY, SECRET_KEY
from db import File

files = Blueprint('files', __name__, static_folder='static')

B62_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


@files.route('/<name>/<key>', methods=['GET'])
def get_file(name, key=None):
    try:
        file_id = FileMapper.b62_decode(name)
        file = File.get(File.id == file_id)

        key, _ = os.path.splitext(key)

        if file.file_key == key:
            response = send_file(FileMapper.get_storage_path(file_id),
                                 mimetype=file.content_type)
            response.headers['Content-Disposition'] = (
                "inline;filename*=UTF-8''{}".format(
                    quote(file.original_filename)))
            return response
    except (ValueError, DoesNotExist):
        abort(404)

    abort(404)


@files.route('/')
def index():
    return files.send_static_file('pshuu.webm')


def url_for_file(file):
    _, file_ext = os.path.splitext(file.original_filename)
    return url_for('files.get_file',
                   name=FileMapper.b62_encode(file.id),
                   key=file.file_key,
                   _external=True) + file_ext


def handle_file_upload(user, file):
    file_mapper = FileMapper(user)
    if not file:
        abort(400)

    # Get ID for file.
    file_entry = File.create(
        user=user,
        original_filename=file.filename,
        content_type=file.content_type or None)

    # Generate file key based on username and ID and update record.
    file_key = file_mapper.get_file_key(file_entry.id)
    file_entry.file_key = file_key
    file_entry.save()

    # Ensure path to save exists and save file.
    storage_path = file_mapper.get_storage_path(file_entry.id)
    storage_dir = os.path.dirname(storage_path)
    if not os.path.exists(storage_dir):
        try:
            os.makedirs(storage_dir, 0o750)
        except OSError:
            # OSError can occur if the directory already exists, so...
            if not os.path.exists(storage_dir):
                raise
    file.save(storage_path)

    return file_entry


def handle_file_delete(file_id=None, file_entry=None):
    try:
        if not file_entry:
            file_entry = File.get(File.id == file_id)

        os.unlink(FileMapper.get_storage_path(file_entry.id))
        file_entry.delete_instance()

        return True
    except DoesNotExist:
        return False


class FileMapper(object):
    """
    Map between the actual name where files are stored, and the URL name/key
    returned to the client.
    """
    FILE_KEY_LENGTH = 6
    DELETE_KEY_LENGTH = 20

    def __init__(self, user):
        self.username = bytes(user.username, 'utf-8')

    def get_file_key(self, file_id):
        h = hmac.new(bytes(SECRET_KEY, 'utf-8'), digestmod=hashlib.sha256)
        h.update(self.username)
        h.update(b'/')
        h.update(bytes((file_id,)))
        h = h.digest()
        return str(urlsafe_b64encode(h)[:self.FILE_KEY_LENGTH], 'utf8')

    @staticmethod
    def get_delete_key(file_id):
        h = hmac.new(bytes(SECRET_KEY, 'utf-8'), digestmod=hashlib.sha256)
        h.update(bytes((file_id,)))
        h = h.digest()
        return str(urlsafe_b64encode(h)[:FileMapper.DELETE_KEY_LENGTH], 'utf8')

    @staticmethod
    def get_storage_path(file_id):
        file_id = "{:08x}".format(file_id)
        return os.path.join(
            UPLOAD_DIRECTORY, file_id[:2], file_id[2:4], file_id[4:])

    @staticmethod
    def b62_encode(number):
        encoded = ''
        while number > 0:
            encoded = B62_ALPHABET[number % 62] + encoded
            number //= 62
        return encoded

    @staticmethod
    def b62_decode(string):
        decoded = sum([
            B62_ALPHABET.index(i) * pow(62, power)
            for power, i in enumerate(string[::-1])])
        if decoded < 0:
            raise ValueError('string not b62')
        return decoded
