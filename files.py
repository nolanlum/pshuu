import hashlib
import hmac
import os
from base64 import urlsafe_b64encode

from flask import Blueprint, abort, send_file
from peewee import DoesNotExist

from config import UPLOAD_DIRECTORY, SECRET_KEY
from db import File

files = Blueprint('files', __name__, template_folder='templates',
                  static_folder='static')

B62_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


@files.route('/<name>/<key>', methods=['GET'])
def get_file(name, key):
    try:
        file_id = FileMapper.b62_decode(name)
        file = File.get(File.id == file_id)
        if file.file_key is None or file.file_key == key:
            return send_file(
                FileMapper.get_storage_path(file_id),
                mimetype=file.content_type)
    except (ValueError, DoesNotExist):
        abort(404)

    abort(404)


@files.route('/')
def index():
    return files.send_static_file('pshuu.webm')


class FileMapper(object):
    """
    Map between the actual name where files are stored, and the URL name/key
    returned to the client.
    """
    FILE_KEY_LENGTH = 6

    def __init__(self, user):
        self.username = bytes(user.username, 'utf-8')

    def get_file_key(self, file_id):
        h = hmac.new(bytes(SECRET_KEY, 'utf-8'), digestmod=hashlib.sha256)
        h.update(self.username)
        h.update(b'/')
        h.update(bytes((file_id,)))
        h = h.digest()
        return urlsafe_b64encode(h)[:self.FILE_KEY_LENGTH]

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
