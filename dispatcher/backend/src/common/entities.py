from dataclasses import dataclass


@dataclass
class DockerImage:
    name: str
    tag: str


@dataclass
class ScheduleConfig:
    task_name: str
    warehouse_path: str
    image: DockerImage
    resources: dict
    flags: dict
