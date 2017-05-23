import time, json, subprocess, sys
from urllib import request, response, parse
from celery import Celery, Task


app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672')


@app.task(bind=True, name='subprocess')
def subprocess_run(self, command: str):
    def update_status(status:str, stdout: str, stderr: str):
        url = 'http://proxy/api/task/' + self.request.id
        payload = {
            'status': status,
            'command': command,
            'stdout': stdout, 
            'stderr': stderr
        }
        req = request.Request(url,
                              headers={'content-type': 'application/json'},
                              data=json.dumps(payload).encode('utf-8'))
        with request.urlopen(req) as response:
            code = response.getcode()
            charset = response.headers.get_content_charset('utf-8')
            body = json.loads(response.read().decode(charset))
            # print('{}, {}'.format(code, body))
            # TODO: retry if a POST failed (code != 200)
    
    def decode_bin_stream(bin) -> str:
        return bin.decode('utf-8') if bin is not None else None

    update_status('STARTED', None, None)
    time.sleep(5)

    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = decode_bin_stream(process.stdout)
    stderr = decode_bin_stream(process.stderr)
    
    update_status('UPLOADING', stdout, stderr)
    time.sleep(5)

    if stderr == '':
        update_status('FINISHED', stdout, stderr)
    else:
        update_status('ERROR', stdout, stderr)

@app.task(bind=True, name='mwoffliner')
def mwoffliner(self, config: dict):
    def update_status(status:str, command: str=None, returncode: int=None, stdout: str=None, stderr: str=None, error: str=None):
        url = 'http://proxy/api/task/' + self.request.id
        payload = {
            'status': status,
            'command': command,
            'returncode': returncode,
            'stdout': stdout,
            'stderr': stderr,
            'error': error
        }
        req = request.Request(url,
                              headers={'content-type': 'application/json'},
                              data=json.dumps(payload).encode('utf-8'))
        with request.urlopen(req) as response:
            code = response.getcode()
            charset = response.headers.get_content_charset('utf-8')
            body = json.loads(response.read().decode(charset))
            # print('{}, {}'.format(code, body))
            # TODO: retry if a POST failed (code != 200)
    
    def decode_bin_stream(bin) -> str:
        return bin.decode('utf-8') if bin is not None else None

    def assemble_command(config: dict) -> [str]:
        whitelist = ['mwUrl', 'adminEmail', 'verbose']
        command = ['mwoffliner']
        for key, value in config.items():
            if key not in whitelist:
                raise MWOfflinerConfigKeyError(key)
            command.append("--{}={}".format(key, value))
        return command

    command_str = None
    returncode = None

    try:
        update_status(status='STARTED')

        command = assemble_command(config)
        command_str = ' '.join(command)

        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        returncode = process.returncode
        stdout = decode_bin_stream(process.stdout)
        stderr = decode_bin_stream(process.stderr)

        process.check_returncode()
        update_status(status='UPLOADING', command=command_str, returncode=returncode, stdout=stdout, stderr=stderr)
        time.sleep(5)
        update_status(status='SUCCESS', command=command_str, returncode=returncode, stdout=stdout, stderr=stderr)

    except MWOfflinerConfigKeyError as error:
        update_status(status='ERROR', error=error.message)
    except subprocess.CalledProcessError as error:
        update_status(status='ERROR', command=command_str, returncode=error.returncode,
                      stdout=decode_bin_stream(error.stdout),
                      stderr=decode_bin_stream(error.stderr))
    except:
        message = "Unexpected error: {}".format(sys.exc_info()[0])
        update_status(status='ERROR', command=command_str, returncode=returncode, error=message)
    

class MWOfflinerConfigKeyError(Exception):
    def __init__(self, key: str):
        self.message = 'The flag "{}" for mwoffliner is not supported.'.format(key)


class MWOfflinerUploadError(Exception):
    def __init__(self):
        pass