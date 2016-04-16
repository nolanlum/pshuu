def add_user():
    username = input('Username: ')
    api_key = input('API Key: ')

    from db import User
    User().create(username=username, api_key=api_key).save()


def add_provisioning_key():
    from binascii import hexlify
    from os import urandom
    from db import ProvisioningKey

    key = str(hexlify(urandom(20)), 'utf8').upper()
    ProvisioningKey.create(key=key)

    print(key)


def list_routes():
    from urllib.parse import unquote
    from flask import url_for

    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)

    for line in sorted(output):
        print(line)


if __name__ == '__main__':
    interp_banner = 'Available Management Methods: ' + ', '.join(
        (x for x in dir(__import__('sys').modules['__main__'])
         if not x.startswith('__')))
    interp_locals = globals()
    interp_locals['app'] = __import__('app').create()
    interp_locals['ctx'] = interp_locals['app'].test_request_context()
    interp_locals['ctx'].push()

    __import__('code').interact(banner=interp_banner, local=interp_locals)

