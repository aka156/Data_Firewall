from uuid import UUID
from typing import Dict

from data_quality_firewall.core.models import FileRun, RunStatus


class RunService:

    def __init__(self):
        self._runs: Dict[UUID, FileRun] = {}

    def create_run(self, filename: str) -> FileRun:
        run = FileRun(filename=filename, status=RunStatus.RECEIVED)
        self._runs[run.id] = run
        return run

    def get_run(self, run_id: UUID) -> FileRun | None:
        return self._runs.get(run_id)
