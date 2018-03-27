import os
import sys

from werkzeug.security import generate_password_hash
from cerberus import Validator
from pymongo import ASCENDING

from utils import mongo


class Initializer:
    @staticmethod
    def create_database_indexes():
        mongo.Users().create_index([(mongo.Users.username, ASCENDING)], name='username', unique=True)
        mongo.Users().create_index([(mongo.Users.email, ASCENDING)], name='email', unique=True)
        mongo.Tasks().create_index([('status', ASCENDING)], name='status', unique=False)
        mongo.Tasks().create_index([('created', ASCENDING)], name='created', unique=False)
        mongo.Tasks().create_index([('started', ASCENDING)], name='started', unique=False)
        mongo.Tasks().create_index([('finished', ASCENDING)], name='finished', unique=False)

    @staticmethod
    def create_initial_user():
        username = os.getenv('INIT_USERNAME', 'admin')
        password = os.getenv('INIT_PASSWORD', 'admin_pass')

        users = mongo.Users()
        if users.find_one() is None:
            document = {
                'username': username,
                'password_hash': generate_password_hash(password),
                'is_admin': True
            }
            validator = Validator(mongo.Users.schema)
            if not validator.validate(document):
                sys.exit()
            users.insert_one(document)


if __name__ == "__main__":
    print("Running pre-start initialization...")
    Initializer.create_database_indexes()
    Initializer.create_initial_user()
