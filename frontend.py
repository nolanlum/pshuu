from binascii import hexlify
from os import urandom

from flask import Blueprint
from flask import abort, jsonify, render_template, redirect, request, url_for
from peewee import DoesNotExist, IntegrityError

from db import ProvisioningKey, User

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/provision/<key>', methods=['GET', 'POST'])
def provision(key):
    try:
        key = ProvisioningKey.get(ProvisioningKey.key == key)
    except DoesNotExist:
        abort(404)

    if request.method == 'GET':
        api_key = str(hexlify(urandom(16)), 'utf8').upper()
        return render_template('provision.html', api_key=api_key)
    elif request.method == 'POST':
        if 'username' not in request.form or 'api_key' not in request.form:
            return jsonify(**{'error': 'missing required form field'})

        try:
            user = User.create(username=request.form['username'],
                               api_key=request.form['api_key'])
            key.delete_instance()
        except IntegrityError:
            return jsonify(**{'error': 'duplicate username or API key'})

        return redirect(
            url_for('frontend.provision_sharex', api_key=user.api_key))


@frontend.route('/provision/<api_key>/custom_uploader.json', methods=['GET'])
def provision_sharex(api_key):
    return jsonify(**{
        'Name': 'pshuu.moe',
        'RequestType': 'POST',
        'RequestURL': 'https://pshuu.moe/upload',
        'FileFormName': 'f',
        'Arguments': {'k': api_key},
        'ResponseType': 'Text',
        'URL': '$json:share_url$',
        'DeletionURL': '$json:delete_url$'
    })


@frontend.route('/manage/<api_key>', methods=['GET'])
def manage(api_key):
    return render_template('manage.html', api_key=api_key)
