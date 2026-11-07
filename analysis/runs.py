"""Load experiment runs from analysis/data/<run name>/.

Each run folder holds meta.json and the files start_run.py downloads:
per_second.csv, run_summary.csv and (after pull_cloudwatch.py) cloudwatch.csv.
"""

import json
import os
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Run:
    name: str
    path: str
    meta: dict = field(default_factory=dict)

    def _csv(self, file_name: str) -> pd.DataFrame | None:
        path = os.path.join(self.path, file_name)
        return pd.read_csv(path) if os.path.exists(path) else None

    @property
    def per_second(self) -> pd.DataFrame | None:
        return self._csv("per_second.csv")

    @property
    def summary(self) -> pd.DataFrame | None:
        return self._csv("run_summary.csv")

    @property
    def cloudwatch(self) -> pd.DataFrame | None:
        return self._csv("cloudwatch.csv")

    @property
    def is_dummy(self) -> bool:
        return bool(self.meta.get("dummy"))


def load_runs(data_dir: str) -> list[Run]:
    """Every sub-folder with a meta.json, sorted by name."""
    runs = []
    if not os.path.isdir(data_dir):
        return runs
    for name in sorted(os.listdir(data_dir)):
        meta_path = os.path.join(data_dir, name, "meta.json")
        if os.path.isfile(meta_path):
            with open(meta_path) as f:
                runs.append(Run(name=name, path=os.path.join(data_dir, name), meta=json.load(f)))
    return runs
