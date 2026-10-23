"""Result ownership is explicit, so changing an entity cannot reuse its result."""
from dataclasses import dataclass


@dataclass
class ResultState:
    revision: int = 0
    forecast_rows: object = None

    def invalidate(self):
        self.revision += 1
        self.forecast_rows = None

    def accept(self, revision, rows):
        if revision == self.revision:
            self.forecast_rows = rows
            return True
        return False
