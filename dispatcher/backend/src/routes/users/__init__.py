import flask

from . import user, keys, password


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__('users', __name__, url_prefix='/api/users')

        self.add_url_rule('/', 'list_users', user.list, methods=['GET'])
        self.add_url_rule('/', 'create_user', user.create, methods=['POST'])

        self.add_url_rule('/<string:user>', 'get_user', user.get, methods=['GET'])
        self.add_url_rule('/<string:user>', 'delete_user', user.delete, methods=['DELETE'])

        self.add_url_rule('/<string:user>/keys', 'list_ssh_keys', keys.list, methods=['GET'])
        self.add_url_rule('/<string:user>/keys', 'add_ssh_keys', keys.add, methods=['POST'])
        self.add_url_rule('/<string:user>/keys/<string:fingerprint>',
                          'delete_ssh_keys', keys.delete, methods=['DELETE'])

        self.add_url_rule('/<string:user>/password', 'update_user_password',
                          password.update, methods=['PATCH'])
