import os

from werkzeug.security import generate_password_hash
from pymongo import ASCENDING

import mongo


class Initializer:
    @staticmethod
    def create_database_indexes():
        mongo.Users().create_index([('username', ASCENDING)], name='username', unique=True)
        mongo.Users().create_index([('email', ASCENDING)], name='email', unique=True)
        mongo.Users().create_index('ssh_keys.fingerprint', name='ssh_keys.fingerprint',
                                   partialFilterExpression={'ssh_keys': {'$exists': True}})

        mongo.RefreshTokens().create_index([('token', ASCENDING)], name='token', unique=True)

    @staticmethod
    def create_initial_user():
        username = os.getenv('INIT_USERNAME', 'admin')
        password = os.getenv('INIT_PASSWORD', 'admin_pass')

        users = mongo.Users()
        if users.find_one() is None:
            document = {
                'username': username,
                'password_hash': generate_password_hash(password),
                'scope': {
                    'user_management': {
                        'change_username': True,
                        'change_email': True,
                        'change_password': True
                    },
                    'task': {
                        'create': True,
                        'delete': True,
                    }
                }
            }
            users.insert_one(document)


if __name__ == "__main__":
    print("Running pre-start initialization...")
    Initializer.create_database_indexes()
    Initializer.create_initial_user()
