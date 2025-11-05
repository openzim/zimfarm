import datetime
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow


@dataclass
class TaskConfig:
    """Configuration for a background task with interval-based execution."""

    func: Callable[[OrmSession], None]
    interval: datetime.timedelta
    name: str | None = None
    _last_run: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.fromtimestamp(0).replace(tzinfo=None)
    )

    @property
    def task_name(self) -> str:
        return self.name or self.func.__name__

    def should_run(self, now: datetime.datetime) -> bool:
        """Check if this task should run based on its interval."""
        return now - self._last_run >= self.interval

    def execute(self, session: OrmSession) -> None:
        """Execute the task and update the last run timestamp."""
        self.func(session)
        self._last_run = getnow()
