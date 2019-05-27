import os

from werkzeug.security import generate_password_hash

from common import mongo


class Initializer:
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
    mongo.Users().initialize()
    mongo.Schedules().initialize()
    mongo.Tasks().initialize()
    mongo.Languages().initialize()
    Initializer.create_initial_user()
