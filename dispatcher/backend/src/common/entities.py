from dataclasses import dataclass


@dataclass
class DockerImage:
    name: str
    tag: str


@dataclass
class ScheduleConfig:
    image: DockerImage
    flags: dict
    queue: str
    task_name: str
    warehouse_path: str
