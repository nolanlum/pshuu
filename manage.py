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


if __name__ == '__main__':
    interp_banner = 'Available Management Methods: ' + ', '.join(
        (x for x in dir(__import__('sys').modules['__main__'])
         if not x.startswith('__')))

    __import__('app').create()
    __import__('code').interact(banner=interp_banner, local=globals())

