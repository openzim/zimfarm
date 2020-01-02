import os

from werkzeug.security import generate_password_hash

from common import mongo


class Initializer:
    @staticmethod
    def initialize():
        print("Running pre-start initialization...")
        mongo.Users().initialize()
        mongo.Schedules().initialize()
        mongo.Tasks().initialize()
        mongo.RequestedTasks().initialize()

    @staticmethod
    def create_initial_user():
        username = os.getenv("INIT_USERNAME", "admin")
        password = os.getenv("INIT_PASSWORD", "admin_pass")

        users = mongo.Users()
        if users.find_one() is None:
            print(f"creating initial user `{username}`")
            document = {
                "username": username,
                "password_hash": generate_password_hash(password),
                "scope": {
                    "user_management": {
                        "change_username": True,
                        "change_email": True,
                        "change_password": True,
                    },
                    "task": {"create": True, "delete": True},
                },
            }
            users.insert_one(document)
