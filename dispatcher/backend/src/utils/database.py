import os
from typing import Dict, List

from werkzeug.security import generate_password_hash

import db.models as dbm
from common import mongo
from common.roles import ROLES
from db.engine import Session


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

        with Session.begin() as session:
            count = session.query(dbm.User).count()
            if count == 0:
                print(f"creating initial user `{username}`")
                pgmUser = dbm.User(
                    mongo_val=None,
                    mongo_id=None,
                    username=username,
                    email=None,
                    password_hash=generate_password_hash(password),
                    scope=ROLES.get("admin"),
                )
                session.add(pgmUser)


class KeysExporter:
    @staticmethod
    def _get_keys_int(obj, curPrefix):
        if isinstance(obj, Dict):
            for k, v in obj.items():
                yield f"{curPrefix}{k}"
                yield from KeysExporter._get_keys_int(v, f"{curPrefix}{k}.")
        elif isinstance(obj, List):
            for v in obj:
                yield from KeysExporter._get_keys_int(v, f"{curPrefix}*.")

    @staticmethod
    def get_keys(obj) -> List[str]:
        return set(KeysExporter._get_keys_int(obj, ""))
