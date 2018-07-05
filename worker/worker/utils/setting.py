import os
import sys
import json
from pathlib import Path
from getpass import getpass


class Setting:
    username: str = None
    password: str = None

    dispatcher_host: str = None
    warehouse_host: str = None
    rabbitmq_port: int = None
    warehouse_command_port: int = None

    working_dir: Path = None
    redis_name: str = None

    interactive: bool = False
    container_inside_files_dir: Path = Path('/files')

    @classmethod
    def read_from_cache(cls, path='setting.json'):
        setting = json.load(open(path)) if os.path.isfile(path) else {}
        cls.username = setting.get('username', None)
        cls.password = setting.get('password', None)
        cls.dispatcher_host = setting.get('dispatcher_host', 'farm.openzim.org')
        cls.warehouse_host = setting.get('warehouse_host', 'farm.openzim.org')
        cls.rabbitmq_port = setting.get('rabbitmq_port', 5671)
        cls.warehouse_command_port = setting.get('warehouse_command_port', 21)
        cls.working_dir = Path(setting.get('working_dir', ''))
        cls.redis_name = setting.get('redis_name', 'zimfarm_redis')

    @classmethod
    def prompt_user(cls):
        print("Let's check some settings:\n",
              "* current values are in '[]'\n",
              "* accept current values by pressing enter\n", sep='')

        cls.username = cls.get_input('Username', cls.username)
        cls.password = cls.get_input('Password', cls.password, redact=True)

        cls.dispatcher_host = cls.get_input('Dispatcher Host', cls.dispatcher_host)
        cls.warehouse_host = cls.get_input('Warehouse Host', cls.warehouse_host)
        cls.rabbitmq_port = cls.get_input('Rabbitmq Port', cls.rabbitmq_port, as_int=True)
        cls.warehouse_command_port = cls.get_input('Warehouse Command Port', cls.warehouse_command_port, as_int=True)

        cls.working_dir = Path(cls.get_input('Working Directory', str(cls.working_dir)))
        cls.redis_name = cls.get_input('Redis Container Name', cls.redis_name)

        print('')

    @classmethod
    def get_input(cls, prompt_text, current_value, redact=False, as_int=False):
        input_method = getpass if redact else input

        retries = 3
        while retries > 0:
            if current_value is None:
                value = input_method("{}: ".format(prompt_text))
            else:
                value = input_method("{} [{}]: ".format(prompt_text, '*' * 8 if redact else current_value))

            # check input
            if len(value) > 0:
                if as_int:
                    try:
                        return int(value)
                    except ValueError:
                        print("Error: input not valid, please retry")
                        retries -= 1
                        continue
                else:
                    return value
            else:
                if current_value is None:
                    print("Error: a value has to be provided to {}.".format(prompt_text.lower()))
                    retries -= 1
                    continue
                else:
                    return current_value
        else:
            sys.exit("Error: setting check value invalid.\n")

    @classmethod
    def save_to_cache(cls, path='setting.json'):
        with open(path, 'w') as file:
            json.dump({
                'username': cls.username,
                'password': cls.password,
                'dispatcher_host': cls.dispatcher_host,
                'warehouse_host': cls.warehouse_host,
                'rabbitmq_port': cls.rabbitmq_port,
                'warehouse_command_port': cls.warehouse_command_port,
                'working_dir': str(cls.working_dir),
                'redis_name': cls.redis_name,
            }, file)

    @classmethod
    def read_from_env(cls):
        cls.username = os.getenv('USERNAME', None)
        cls.password = os.getenv('PASSWORD', None)
        cls.dispatcher_host = os.getenv('DISPATCHER_HOST', 'farm.openzim.org')
        cls.warehouse_host = os.getenv('WAREHOUSE_HOST', 'farm.openzim.org')
        cls.rabbitmq_port = os.getenv('RABBITMQ_PORT', 5671)
        cls.warehouse_command_port = os.getenv('WAREHOUSE_COMMAND_PORT', 21)
        cls.working_dir = Path(os.getenv('WORKING_DIR', ''))
        cls.redis_name = os.getenv('REDIS_NAME', 'zimfarm_redis')

        print('Checking Settings...')

        if Setting.username is None:
            print('Error: USERNAME environmental variable is required.')
            sys.exit(1)
        if Setting.password is None:
            print('Error: PASSWORD environmental variable is required.')
            sys.exit(1)
