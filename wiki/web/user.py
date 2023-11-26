"""
    User classes & helpers
    ~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import json
import binascii
import hashlib
from functools import wraps

from flask import current_app
from flask_login import current_user
from wiki import DataAccessObject



class UserManager(object):
    """A very simple user Manager, that saves it's data as json."""
    def __init__(self):
        self.collection = DataAccessObject.db.Users

    def add_user(self, name, password,
                 active=True, roles=[], authentication_method=None):
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        new_user = {
            'name': name,
            'active': active,
            'roles': roles,
            'authentication_method': authentication_method,
            'authenticated': False
        }

        if authentication_method == 'hash':
            new_user['hash'] = make_salted_hash(password)
        elif authentication_method == 'cleartext':
            new_user['password'] = password
        else:
            raise NotImplementedError(authentication_method)

        userdata = self.collection.insert_one(new_user)
        return User(self, name, userdata)

    def get_user(self, name):
        userdata = self.collection.find_one({"name": name})

        if not userdata:
            return None
        return User(self, name, userdata)

    def delete_user(self, name):
        user = self.collection.delete_one({"name": name})
        if not user:
            return False
        return True

    def update(self, name, userdata):
        self.collection.update_one({"name": name}, {"$set": userdata})


class User(object):
    def __init__(self, manager, name, data):
        self.manager = manager
        self.name = name
        self.data = data

    def get(self, option):
        return self.data.get(option)

    def set(self, option, value):
        self.data[option] = value
        self.save()

    def save(self):
        self.manager.update(self.name, self.data)

    def is_authenticated(self):
        return self.data.get('authenticated')

    def is_active(self):
        return self.data.get('active')

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.name

    def check_password(self, password):
        """Return True, return False, or raise NotImplementedError if the
        authentication_method is missing or unknown."""
        authentication_method = self.data.get('authentication_method', None)
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        # See comment in UserManager.add_user about authentication_method.
        if authentication_method == 'hash':
            result = check_hashed_password(password, self.get('hash'))
        elif authentication_method == 'cleartext':
            result = (self.get('password') == password)
        else:
            raise NotImplementedError(authentication_method)
        return result


def get_default_authentication_method():
    return current_app.config.get('DEFAULT_AUTHENTICATION_METHOD', 'cleartext')


def make_salted_hash(password, salt=None):
    if not salt:
        salt = os.urandom(64)
    d = hashlib.sha512()
    d.update(salt[:32])
    d.update(password)
    d.update(salt[32:])
    return binascii.hexlify(salt) + d.hexdigest()


def check_hashed_password(password, salted_hash):
    salt = binascii.unhexlify(salted_hash[:128])
    return make_salted_hash(password, salt) == salted_hash


def protect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_app.config.get('PRIVATE') and not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        return f(*args, **kwargs)
    return wrapper
