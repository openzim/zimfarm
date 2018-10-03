import os
import sys

from werkzeug.security import generate_password_hash
from pymongo import ASCENDING

from utils import mongo


class Initializer:
    @staticmethod
    def create_database_indexes():
        mongo.Users().create_index([(mongo.Users.username, ASCENDING)], name='username', unique=True)
        mongo.Users().create_index([(mongo.Users.email, ASCENDING)], name='email', unique=True)
        mongo.Users().create_index('ssh_keys.fingerprint', name='ssh_keys.fingerprint', unique=True,
                                   partialFilterExpression={
                                       'ssh_keys': {'$exists': True}
                                   })

        mongo.RefreshTokens().create_index([('token', ASCENDING)], name='token', unique=True)

        mongo.Tasks().create_index([('status', ASCENDING)], name='status', unique=False)
        mongo.Tasks().create_index([('timestamp.creation', ASCENDING)], name='timestamp.creation', unique=False)
        mongo.Tasks().create_index([('timestamp.termination', ASCENDING)], name='timestamp.termination', unique=False)
        mongo.Tasks().create_index([('offliner.name', ASCENDING)], name='offliner.name', unique=False)

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
