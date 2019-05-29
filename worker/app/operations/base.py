import asyncio
from dataclasses import dataclass
from typing import Optional

from aiodocker.containers import DockerContainer
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class Operation:
    """Base class for all operations"""

    def __init__(self):
        pass

    def execute(self):
        pass

    @staticmethod
    async def detect_stuck(container: DockerContainer, max_wait: int = 600):
        histories = []
        interval = 60
        while True:
            latest = await container.log(stdout=True, stderr=False, tail=100)
            histories.append(latest)
            if len(histories) > max_wait / interval:
                earliest = histories.pop(0)
                if earliest == latest:
                    logger.info(f'Detected container stuck. Terminating...')
                    await container.kill()
                    break
            await asyncio.sleep(interval)


@dataclass()
class ContainerResult:
    image_name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str

    def is_successful(self):
        return self.exit_code == 0

    def __repr__(self):
        exit_code_description = 'zero' if self.exit_code == 0 else 'non-zero'
        return (f'Command {self.command} in image {self.image_name} returned '
                f'with {exit_code_description} exit code {self.exit_code}.')


class OperationError(Exception):
    def to_dict(self):
        return {}


class UploadError(OperationError):
    def __init__(self, code: str, message: Optional[str] = None):
        self.code = code
        self.message = message

    def to_dict(self):
        return {
            'code': self.code,
            'message': self.message,
        }
