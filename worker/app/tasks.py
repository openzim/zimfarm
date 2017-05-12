import time, json, subprocess, sys
from urllib import request, response, parse
from celery import Celery, Task


app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672', backend='redis://redis:6379/0')


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
    def update_status(status:str, command: str=None, stdout: str=None, error: str=None):
        url = 'http://proxy/api/task/' + self.request.id
        payload = {
            'status': status,
            'command': command,
            'stdout': stdout, 
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

    whitelist = ['mwUrl', 'adminEmail']
    # t = `mwoffliner  --mwUrl=https://bm.wikipedia.org/ --adminEmail=kelson@kiwix.org --verbose`
    try:
        update_status('STARTED')

        command = ['mwoffliner']
        for key, value in config.items():
            if key not in whitelist:
                raise MWOfflinerConfigKeyError(key)
            command.append("--{}={}".format(key, value))
        command_str = ' '.join(command)

        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = decode_bin_stream(process.stdout)
        stderr = decode_bin_stream(process.stderr)

        if stderr == '' or stderr is None:
            update_status('UPLOADING', command_str, stdout, stderr)
            time.sleep(5)
            update_status('FINISHED', command_str, stdout, stderr)
        else:
            raise MWOfflinerExecutionError(stderr)
    except MWOfflinerConfigKeyError as error:
        update_status('Config ERROR', error=error.message)
    except MWOfflinerExecutionError as error:
        update_status('Execution ERROR', error=error.stderr)
    except:
        message = "Unexpected error: {}".format(sys.exc_info()[0])
        update_status('ERROR', error=message)
    

class MWOfflinerConfigKeyError(Exception):
    def __init__(self, key: str):
        self.message = 'The flag "{}" for mwoffliner is not supported.'.format(key)


class MWOfflinerExecutionError(Exception):
    def __init__(self, stderr: str):
        self.stderr = stderr


class MWOfflinerUploadError(Exception):
    def __init__(self):
        pass