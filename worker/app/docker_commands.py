import subprocess


def pull(container_name: str):
    process = subprocess.run(["docker", "pull", container_name], encoding='utf-8', check=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process.stdout, process.stderr, process.returncode


def run(container_name: str):
    pass